from enum import Enum
from pymodbus.constants import Endian
from datetime import datetime


class DataType(Enum):
    INT = 1
    UINT = 2
    FLOAT = 3


class DataHolder:
    @classmethod
    def from_config(cls, config: [dict]):
        raise NotImplementedError

    def __init__(self, mpid: str, remark: str, factor: float = 1, offset: int = 0, reground: int = None, value=0,
                 lastval: datetime = None):
        self.mpid = mpid
        self.remark = remark
        self.factor = factor
        self.offset = offset
        self.reground = reground
        self.value = value
        self.lastval = lastval


class Register(DataHolder):
    @classmethod
    def from_config(cls, config: [dict]):
        registers = []

        for reg in config:
            mpid = reg["mpid"]
            remark = reg["remark"]
            factor = float(reg.get("factor", 1))
            offset = int(reg.get("offset", 0))
            reground = reg.get("round", None)

            if reground == "":
                reground = None

            if reground is not None:
                reground = int(reground)

            rstart = int(reg["rstart"])
            rcount = int(reg["rcount"])
            rtype = reg["rtype"]
            endian = reg["endian"]

            if rtype == "int":
                rtype = DataType.INT
            elif rtype == "uint":
                rtype = DataType.UINT
            elif rtype == "float":
                rtype = DataType.FLOAT
            else:
                raise InvalidDataTypeException(rtype)

            if endian == "big":
                endian = Endian.Big
            elif endian == "little":
                endian = Endian.Little
            else:
                raise InvalidEndianTypeException(endian)

            registers.append(Register(mpid, remark, rstart, rcount, rtype, endian, factor, offset, reground))

        return registers

    def __init__(self, mpid: str, remark: str, rstart: int, rcount: int, rtype: DataType, endian: Endian,
                 factor: float = 1, offset: int = 0, reground: int = None, value=0, lastval: datetime = None):
        super().__init__(mpid, remark, factor, offset, reground, value, lastval)
        self.rstart = rstart
        self.rcount = rcount
        self.rtype = rtype
        self.endian = endian


class DataRecord(DataHolder):
    @classmethod
    def from_config(cls, config: [dict]):
        datarecords = []

        for dr in config:
            mpid = dr["mpid"]
            remark = dr["remark"]
            factor = float(dr.get("factor", 1))
            offset = int(dr.get("offset", 0))
            reground = dr.get("round", None)

            if reground == "":
                reground = None

            if reground is not None:
                reground = int(reground)

            record_id = dr["record_id"]

            datarecords.append(DataRecord(mpid, remark, record_id, factor, offset, reground))

        return datarecords

    def __init__(self, mpid: str, remark: str, record_id: int,
                 factor: float = 1, offset: int = 0, reground: int = None, value=0, lastval: datetime = None):
        super().__init__(mpid, remark, factor, offset, reground, value, lastval)
        self.record_id = record_id


class InvalidEndianTypeException(Exception):
    pass


class InvalidDataTypeException(Exception):
    pass
