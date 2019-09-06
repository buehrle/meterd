import logging
import sys
import datetime


class SystemdHandler(logging.Handler):
    # http://0pointer.de/public/systemd-man/sd-daemon.html
    PREFIX = {
        # EMERG <0>
        # ALERT <1>
        logging.CRITICAL: "<2>",
        logging.ERROR: "<3>",
        logging.WARNING: "<4>",
        # NOTICE <5>
        logging.INFO: "<6>",
        logging.DEBUG: "<7>",
        logging.NOTSET: "<7>"
    }

    def __init__(self, stream=sys.stdout):
        self.stream = stream
        logging.Handler.__init__(self)

    def emit(self, record):
        try:
            msg = self.PREFIX[record.levelno] + self.format(record) + "\n"
            self.stream.write(msg)
            self.stream.flush()
        except Exception:
            self.handleError(record)


class MonitoringHandler(logging.Handler):
    PREFIX = {
        logging.INFO: "INFO",
        logging.WARNING: "WARN",
        logging.ERROR: "ERR"
    }

    def __init__(self, server):
        self.server = server
        logging.Handler.__init__(self)

    def emit(self, record):
        try:
            now = datetime.datetime.now()
            self.server.add_log("{} {}: {}".format(now.strftime("%H:%M:%S"), self.PREFIX[record.levelno],
                                                   self.format(record)))
        except Exception:
            self.handleError(record)
