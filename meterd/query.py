import time
import logging
import socket
import os
import serial
import lib.meterbus as mbus
from lib.meterbus import MBusFrameDecodeError
from serial.serialutil import SerialException
from enum import Enum
from data import Register, DataType, DataHolder, DataRecord
from threading import Lock
from pymodbus.client.sync import ModbusTcpClient, ModbusSerialClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
from pymodbus.exceptions import ConnectionException
from pymodbus.register_read_message import ReadHoldingRegistersResponse
from datetime import datetime


class QueryProtocol(Enum):
    MODBUS_TCP = 1
    MODBUS_RTU = 2
    MBUS = 3


class NoACKResponseError(Exception):
    pass


# An abstract superclass for all protocols
class Query:
    __locks = {}

    @classmethod
    def _get_lock(cls, resource):
        if resource in cls.__locks:
            logging.info("I have a lock for {}.".format(resource))
            return cls.__locks[resource]
        else:
            logging.info("Creating a lock for {}.".format(resource))
            lock = Lock()
            cls.__locks.update({resource: lock})
            return lock

    def __init__(self, tpid: str, query_interval: int, dataholders: [DataHolder], unitid: int, protocol: QueryProtocol):
        self.tpid = tpid                  # Unique ID of the queried meter
        self.query_interval = query_interval
        self.dataholders = dataholders
        self.protocol = protocol          # Modbus-TCP, Modbus-RTU or MBus
        self.unitid = unitid              # The Bus ID of the meter
        self.stop = False
        self._counter = 0

    def do(self, sleeptime: float, interval: int):
        retval = False

        if self._counter == 0:
            retval = True

        self._counter += 1

        if self._counter >= (interval / sleeptime):
            self._counter = 0

        time.sleep(sleeptime)

        return retval

    def serve(self):
        raise NotImplementedError()


class ModbusQuery(Query):
    def __init__(self, tpid: str, query_interval: int, registers: [Register], unitid: int, protocol: QueryProtocol,
                 register_offset: int = 0):
        super().__init__(tpid, query_interval, registers, unitid, protocol)
        self.register_offset = register_offset

    def _iterate_registers(self, client):
        for register in self.dataholders:
            try:
                result = client.read_holding_registers(address=register.rstart + self.register_offset,
                                                       count=register.rcount, unit=self.unitid)

                # pymodbus doesn't raise an exception but returns it. ???
                if not isinstance(result, ReadHoldingRegistersResponse):
                    raise Exception(str(result))

                rcount_tmp = register.rcount

                # If the register count is 3, add 16 null bits to the MSB side
                if rcount_tmp == 3:
                    if register.endian == Endian.Big:
                        result.registers.insert(0, 0)
                    elif register.endian == Endian.Little:
                        result.registers.append(0)

                    rcount_tmp += 1

                decoder = BinaryPayloadDecoder.fromRegisters(result.registers, byteorder=register.endian)

                if rcount_tmp == 1:
                    if register.rtype == DataType.INT:
                        register.value = decoder.decode_16bit_int()
                    elif register.rtype == DataType.UINT:
                        register.value = decoder.decode_16bit_uint()
                elif rcount_tmp == 2:
                    if register.rtype == DataType.INT:
                        register.value = decoder.decode_32bit_int()
                    elif register.rtype == DataType.UINT:
                        register.value = decoder.decode_32bit_uint()
                    elif register.rtype == DataType.FLOAT:
                        register.value = decoder.decode_32bit_float()
                elif rcount_tmp == 4:
                    if register.rtype == DataType.INT:
                        register.value = decoder.decode_64bit_int()
                    elif register.rtype == DataType.UINT:
                        register.value = decoder.decode_64bit_uint()
                    elif register.value == DataType.FLOAT:
                        register.value = decoder.decode_64bit_float()

                register.value *= register.factor
                register.value += register.offset

                if register.reground is not None:
                    register.value = round(register.value, register.reground)

                register.lastval = datetime.utcnow()
            except Exception as e:
                logging.warning("{} occured while reading register(s) {} on device {}. Retrying in {}s."
                                .format(e.__class__.__name__, register.mpid, self.tpid, self.query_interval))

    def serve(self):
        raise NotImplementedError()


class ModbusTCPQuery(ModbusQuery):
    def __init__(self, tpid: str, query_interval: int, registers: [Register], unitid: int, address: str,
                 register_offset: int = 0):
        super().__init__(tpid, query_interval, registers, unitid, QueryProtocol.MODBUS_TCP, register_offset)

        self.address = address
        self.lock = super()._get_lock(address)

    def serve(self):
        while not self.stop:
            if self.do(0.1, self.query_interval):
                with self.lock:
                    logging.info("Querying Modbus-TCP device {}.".format(self.tpid))

                    try:
                        with ModbusTcpClient(self.address, timeout=10) as client:
                            self._iterate_registers(client)
                    except (socket.error, ConnectionException):
                        logging.warning("Could not connect to Modbus-TCP client on {}. Retrying in {}s."
                                        .format(self.tpid, self.query_interval))


class ModbusRTUQuery(ModbusQuery):
    def __init__(self, tpid: str, query_interval: int, registers: [Register], unitid: int, device: str,
                 baudrate: int, parity: str, register_offset: int = 0):
        super().__init__(tpid, query_interval, registers, unitid, QueryProtocol.MODBUS_RTU, register_offset)

        self.device = device
        self.baudrate = baudrate
        self.parity = parity
        self.lock = super()._get_lock(device)

    def serve(self):
        while not self.stop:
            if self.do(0.1, self.query_interval):
                with self.lock:
                    logging.info("Querying Modbus-RTU device {}.".format(self.tpid))

                    try:
                        if not os.access(self.device, os.R_OK | os.W_OK):
                            raise PermissionError()

                        with ModbusSerialClient(method="rtu", port=self.device, baudrate=self.baudrate,
                                                parity=self.parity, timeout=1) as client:
                            self._iterate_registers(client)
                    except PermissionError:
                        logging.warning("Cannot access device {}: No permissions or device doesn't exist. "
                                        "Please check if your udev-rules are set correctly. Retrying in {}s."
                                        .format(self.device, self.query_interval))
                    except ConnectionException:
                        logging.warning("Could not connect to Modbus-RTU client on {}. Retrying in {}s."
                                        .format(self.tpid, self.query_interval))


class MBusQuery(Query):
    def __init__(self, tpid: str, query_interval: int, datarecords: [DataRecord], unitid: int, device: str,
                 baudrate: int, parity: str, converter_echo: bool):
        super().__init__(tpid, query_interval, datarecords, unitid, QueryProtocol.MBUS)

        self.device = device
        self.baudrate = baudrate
        self.parity = parity
        self.converter_echo = converter_echo
        self.lock = super()._get_lock(device)

    def serve(self):
        while not self.stop:
            if self.do(0.1, self.query_interval):
                with self.lock:
                    logging.info("Querying MBus device {}.".format(self.tpid))

                    try:
                        if not os.access(self.device, os.R_OK | os.W_OK):
                            raise PermissionError()

                        ibt = mbus.inter_byte_timeout(self.baudrate)

                        with serial.Serial(port=self.device, baudrate=self.baudrate, bytesize=8, parity=self.parity,
                                           stopbits=1, timeout=2, inter_byte_timeout=ibt) as ser:
                            # -- First check if this MBUS device is reachable
                            mbus.send_ping_frame(ser, self.unitid)

                            if self.converter_echo:
                                mbus.recv_frame(ser)

                            frame = mbus.load(mbus.recv_frame(ser))

                            # We expect an ACK response
                            if not isinstance(frame, mbus.TelegramACK):
                                raise NoACKResponseError()

                            # -- Next, request the first few records and save the request
                            req = mbus.send_request_frame_multi(ser, self.unitid)

                            if self.converter_echo:
                                mbus.recv_frame(ser)

                            frame = mbus.load(mbus.recv_frame(ser))

                            if not isinstance(frame, mbus.TelegramLong):
                                raise MBusFrameDecodeError("")

                            while frame.more_records_follow:
                                time.sleep(0.1)

                                # Toggle the Frame Count Bit bit to indicate that we received the previous telegram
                                req.header.cField.parts[0] ^= mbus.CONTROL_MASK_FCB
                                req = mbus.send_request_frame_multi(ser, self.unitid, req)

                                if self.converter_echo:
                                    mbus.recv_frame(ser)

                                frame += mbus.load(mbus.recv_frame(ser))

                            for rec_record in frame.records:
                                rec_id = "{} {}".format(str(rec_record.dib), str(rec_record.vib))

                                for datarecord in self.dataholders:
                                    if datarecord.record_id.lower() == rec_id.lower():
                                        datarecord.value = float(rec_record.parsed_value)
                                        datarecord.value *= datarecord.factor
                                        datarecord.value += datarecord.offset

                                        if datarecord.reground is not None:
                                            datarecord.value = round(datarecord.value, datarecord.reground)

                                        datarecord.lastval = datetime.utcnow()

                    except NoACKResponseError:
                        logging.warning("Can't reach MBUS unit {} on device {}. Maybe you set the wrong unit ID?"
                                        .format(self.unitid, self.device))
                    except MBusFrameDecodeError:
                        logging.warning("Unexpected reply from device {}. Retrying in {}s."
                                        .format(self.device, self.query_interval))
                    except SerialException:
                        logging.warning("Serial connection on {} seems to be broken. Retrying in {}s."
                                        .format(self.device, self.query_interval))
                    except PermissionError:
                        logging.warning("Cannot access device {}: No permissions or device doesn't exist. "
                                        "Please check if your udev-rules are set correctly. Retrying in {}s."
                                        .format(self.device, self.query_interval))
