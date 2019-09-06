import socket
import logging
import os
from query import Query
from datetime import datetime, timedelta


class MonitoringServer:
    def __init__(self, main_thread, meters: [Query]):
        self.meters = meters
        self.main_thread = main_thread
        self.stop = False
        self.main_heartbeat = datetime.utcnow()
        self.loglist = []
        self.valuelist = {}

    def add_log(self, message):
        if len(self.loglist) >= 20:
            self.loglist.pop(0)

        self.loglist.append(message)

    def add_value(self, device: str, values: list):
        self.valuelist[device] = values

    def run(self):
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.settimeout(0.1)  # Make sure the loop is never blocked
        server.bind("\0meterd")  # Bind to a file in the abstract unix namespace
        server.listen(1)

        while not self.stop:
            now = datetime.utcnow()

            if now - self.main_heartbeat > timedelta(seconds=10):
                logging.error("Main thread seems to be dead as it didn't answer for 10 seconds. Killing myself.")
                self.stop = True
                self.main_thread.interrupted = True

                for meter in self.meters:
                    meter.stop = True

            try:
                conn, add = server.accept()

                with conn:
                    with conn.makefile(mode="rw", encoding="utf-8") as cf:
                        try:
                            query = cf.readline().strip()

                            logging.debug("Received query on monitoring server: {}".format(query))

                            query = query.split(" ")

                            command = query[0]

                            if command == "devcount":  # 1: Total amount of devices
                                cf.write(str(len(self.meters)))
                            elif command == "olderthan":  # 2: Amount of not queried devices
                                hours = int(query[1])
                                minutes = int(query[2])

                                errors = 0

                                for meter in self.meters:
                                    for dataholder in meter.dataholders:
                                        if dataholder.lastval is not None:
                                            if now - dataholder.lastval < timedelta(minutes=minutes, hours=hours):
                                                continue
                                        errors += 1
                                        break

                                cf.write(str(errors))
                            elif command == "alive":
                                cf.write("TRUE")
                            elif command == "restart":
                                logging.info("A restart has been requested. Telling the main thread.")
                                self.main_thread.interrupt(os.EX_OK)
                            elif command == "log":
                                for message in self.loglist:
                                    cf.write("{}\n".format(message))
                            elif command == "values":
                                if len(query) > 1:
                                    device = query[1]

                                    if device in self.valuelist:
                                        for val_info in self.valuelist[device]:
                                            mpid, lastval, value = val_info

                                            if lastval is not None:
                                                lastval = lastval.isoformat()

                                            cf.write("{}|{}|{}\n".format(lastval, mpid, value))
                                else:
                                    for device in self.valuelist.keys():
                                        cf.write("{}\n".format(device))
                            else:
                                raise CommandNotExistingError()

                            cf.flush()
                        except CommandNotExistingError:
                            cf.write("Unknown command!")
                            cf.flush()
                        except (IndexError, TypeError):
                            pass
            except socket.timeout:
                pass
            except Exception as e:
                logging.warning("Error in the monitoring server.", exc_info=e)

        server.close()


class CommandNotExistingError(Exception):
    pass
