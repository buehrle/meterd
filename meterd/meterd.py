#!/usr/local/meterd/venv/bin/python3

# Daemon for querying meters through MBus, RTU-Modbus and TCP-Modbus
# Florian Buehrle 2019

import os
import signal
import threading
import time
import lib.yaml as yaml
import fcntl
import datetime
import logging
from lib.yaml import Loader
from lib.yaml.scanner import ScannerError
from query import ModbusTCPQuery, ModbusRTUQuery, MBusQuery
from data import Register, DataRecord, InvalidEndianTypeException, InvalidDataTypeException
from xml.etree import ElementTree
from handlers import SystemdHandler, MonitoringHandler
from monitoring import MonitoringServer


class Meterd:
    def __init__(self):
        self.__exitcode = os.EX_OK
        self.__interrupted = False

        self.masterpath = "/etc/meterd/"
        self.meters = []

        self.xmlpath = ""
        self.save_interval = 15
        self.id = ""
        self.sn = ""
        self.ip = ""

        signal.signal(signal.SIGINT, self.sig_handle)

        try:
            with open(self.masterpath + "main.yaml", 'r') as maincfg:
                cfg = yaml.load(maincfg, Loader=Loader)

                cfg_main = cfg["main"]

                self.xmlpath = cfg_main["xmlpath"]
                self.save_interval = cfg_main["save_interval"]
                self.id = cfg_main["id"]
                self.sn = cfg_main["sn"]
                self.ip = cfg_main["ip"]

                if not self.xmlpath or not self.save_interval or not self.id or not self.sn or not self.ip:
                    raise KeyError()
        except FileNotFoundError:
            logging.error("Main config file not found.")
            exit(os.EX_CONFIG)
        except (KeyError, ScannerError):
            logging.error("Invalid main config file.")
            exit(os.EX_CONFIG)

        # Parse the config files
        for r, d, f in os.walk(self.masterpath + "conf.d/", followlinks=False):
            for file in f:
                try:
                    with open(r + file, 'r') as metercfg:
                        cfg = yaml.load(metercfg, Loader=Loader)

                        cfg_basic = cfg["basic"]

                        # These settings are the same for both MBus and Modbus
                        protocol = cfg_basic["protocol"]
                        tpid = cfg_basic["tpid"]
                        unit = int(cfg_basic["unit"])
                        query_interval = int(cfg_basic["query_interval"])

                        query = None

                        if protocol == "modbus_tcp":
                            registers = Register.from_config(cfg["registers"])
                            address = cfg_basic["address"]
                            register_offset = int(cfg_basic["register_offset"])

                            query = ModbusTCPQuery(tpid, query_interval, registers, unit, address, register_offset)
                        elif protocol == "modbus_rtu":
                            registers = Register.from_config(cfg["registers"])
                            register_offset = int(cfg_basic["register_offset"])
                            device = cfg_basic["device"]
                            baudrate = int(cfg_basic["baudrate"])
                            parity = cfg_basic["parity"]

                            query = ModbusRTUQuery(tpid, query_interval, registers, unit, device, baudrate, parity,
                                                   register_offset)
                        elif protocol == "mbus":
                            datarecords = DataRecord.from_config(cfg["records"])
                            device = cfg_basic["device"]
                            baudrate = int(cfg_basic["baudrate"])
                            parity = cfg_basic["parity"]
                            converter_echo = bool(cfg_basic["converter_echo"])

                            query = MBusQuery(tpid, query_interval, datarecords, unit, device, baudrate, parity,
                                              converter_echo)
                        else:
                            logging.error("Invalid protocol type \"{}\" in file {}. "
                                          "Maybe this protocol will be supported in future versions."
                                          .format(protocol, file))
                            exit(os.EX_CONFIG)

                        self.meters.append(query)
                except InvalidDataTypeException as e:
                    logging.error("Invalid register data type \"{}\" in file {}.".format(str(e), file))
                    exit(os.EX_CONFIG)
                except InvalidEndianTypeException as e:
                    logging.error("Invalid endian type \"{}\" in file {}.".format(str(e), file))
                    exit(os.EX_CONFIG)
                except (KeyError, TypeError):
                    logging.error("Invalid configuration file {}.".format(file))
                    exit(os.EX_CONFIG)
                except (IOError, PermissionError):
                    logging.error("Could not read config file {}.".format(file))
                    exit(os.EX_NOPERM)

    # Handle SIGINT to ensure a graceful exit
    def sig_handle(self, signum, frame):
        self.interrupt(os.EX_OK)

    def interrupt(self, exitcode):
        self.__interrupted = True
        self.__exitcode = exitcode

    def run(self):
        last_minute = -1
        query_threads = []

        monitor = MonitoringServer(self, self.meters)
        monitor_thread = threading.Thread(target=monitor.run)
        monitor_thread.start()

        logging.getLogger().addHandler(MonitoringHandler(monitor))

        logging.info("Started monitoring server on socket @meterd.")

        for meter in self.meters:
            thread = threading.Thread(target=meter.serve)
            query_threads.append(thread)
            thread.start()

        logging.info("Started query threads for {} devices.".format(len(self.meters)))

        while not self.__interrupted:
            now = datetime.datetime.utcnow()
            minute = now.minute

            # Check if threads are still alive
            for t in query_threads:
                if not t.isAlive():
                    logging.error("Fatal error: A query thread has exited.")
                    self.interrupt(os.EX_TEMPFAIL)

            # If the monitor thread stops, a restart has been requested
            if not monitor_thread.isAlive():
                logging.info("Fatal error: The monitor thread has exited.")
                self.interrupt(os.EX_TEMPFAIL)

            # Make last queried values available to the monitoring server
            for meter in self.meters:
                valuelist = []

                for dataholder in meter.dataholders:
                    valuelist.append((dataholder.mpid, dataholder.lastval, dataholder.value))

                monitor.add_value(meter.tpid, valuelist)

            if minute % self.save_interval == 0 and minute != last_minute:  # Save XML file every 15 minutes
                last_minute = minute
                timestamp = now.replace(microsecond=0, tzinfo=datetime.timezone.utc).isoformat()

                logging.info("Saving values to " + self.xmlpath)

                try:
                    if not os.path.exists(self.xmlpath):
                        open(self.xmlpath, 'w+').close()

                    if not os.access(self.xmlpath, os.R_OK | os.W_OK):
                        raise PermissionError()
                except (IOError, PermissionError):
                    logging.warning("Could not write file {}. Please check folder permissions! "
                                    "Retrying in {} minutes.".format(self.xmlpath, self.save_interval))
                    continue

                xmldoc = None

                while xmldoc is None:  # Loops are beautiful
                    try:
                        with open(self.xmlpath, 'r+') as xmlfile:
                            # Try to obtain a UNIX lock on the XML file to ensure the FTP daemon doesn't modify it
                            fcntl.flock(xmlfile, fcntl.LOCK_EX | fcntl.LOCK_NB)

                            try:
                                xmldoc = ElementTree.fromstringlist([line.strip() for line in xmlfile.readlines()])
                            except ElementTree.ParseError:
                                xmldoc = ElementTree.Element("RMCU")

                            for meter in self.meters:
                                values_node = ElementTree.Element("VALUES")

                                for dataholder in meter.dataholders:
                                    if dataholder.lastval is None:
                                        logging.warning("Device {}: Dataholders {} have not been queried yet."
                                                        .format(meter.tpid, dataholder.mpid))
                                    elif now - dataholder.lastval > datetime.timedelta(minutes=self.save_interval):
                                        logging.warning("Device {}: Value of {} is older than {} minutes. "
                                                        "Skipping!".format(meter.tpid, dataholder.mpid,
                                                                           self.save_interval))
                                    else:
                                        ElementTree.SubElement(values_node, dataholder.mpid).text = str(dataholder.value)

                                # Continue if no measurement could be saved
                                if len(list(values_node)) == 0:
                                    ElementTree.SubElement(values_node, "STATUS").text = "2"
                                else:
                                    ElementTree.SubElement(values_node, "STATUS").text = "0"

                                # Add timestamp to this value node
                                timestamp_node = ElementTree.Element("DATETIME")
                                timestamp_node.text = timestamp
                                values_node.insert(0, timestamp_node)

                                # Reuse this device's element if it already exists in the XML tree
                                meter_node = xmldoc.find(".//TP[@ID='{tpid}']".format(tpid=meter.tpid))

                                if meter_node is None:
                                    meter_node = ElementTree.Element("TP", {"ID": meter.tpid})

                                    # New nodes should always be inserted on position 0 in <RMCU>
                                    xmldoc.insert(0, meter_node)

                                meter_node.append(values_node)

                            # Insert data about the collector device at the bottom
                            for tag, val in [("ID", self.id), ("SN", self.sn), ("IP", self.ip)]:
                                info_node = xmldoc.find(".//" + tag)

                                if info_node is None:
                                    info_node = ElementTree.SubElement(xmldoc, tag)

                                info_node.text = str(val)

                            # Jump to the beginning of the file and rewrite it
                            xmlfile.seek(0)
                            xmlfile.truncate()

                            # Compile the XML tree and write it
                            xmlfile.write(ElementTree.tostring(xmldoc, encoding="utf-8").decode("utf-8"))

                            # Release the file lock
                            fcntl.flock(xmlfile, fcntl.LOCK_UN)
                    except BlockingIOError:
                        logging.warning("The XML file is locked. Retrying in 1s...")
                        time.sleep(1)

                logging.info("Success.")

            monitor.main_heartbeat = now
            time.sleep(0.1)

        # Notify all threads that the program is about to stop
        for meter in self.meters:
            meter.stop = True

        monitor.stop = True

        logging.info("Shutting down...")

        for thread in query_threads:
            thread.join()

        monitor_thread.join()

        logging.info("Goodbye.")

        exit(self.__exitcode)


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel("INFO")

    while logger.handlers:
        logger.handlers.pop()

    logger.addHandler(SystemdHandler())

    Meterd().run()
