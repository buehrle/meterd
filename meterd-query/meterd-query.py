#!/usr/local/meterd/venv/bin/python3

# Daemon for querying meters through MBus, RTU-Modbus and TCP-Modbus
# Florian Buehrle 2019

import os
import sys
import socket


class MeterdQuery:
    def __init__(self, arguments):
        self.oid = ""
        self.arguments = arguments

        try:
            if len(arguments) < 2:
                raise IndexError()

            for i, arg in enumerate(arguments):
                if arg == "-g":
                    self.oid = arguments[i + 1]
        except IndexError:
            print("Invalid arguments.")
            exit(1)

    def start(self):
        connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        try:
            connection.connect("\0meterd")

            with connection.makefile(mode="rw", encoding="utf-8") as cf:
                if self.oid == "":
                    cf.write(" ".join(self.arguments[1:]) + "\n")
                    cf.flush()

                    for line in cf:
                        print(line.strip())
                else:
                    try:
                        parser = OidParser(self.oid)
                        parser.eat(20)

                        command = parser.eat()

                        if command == "1":
                            cf.write("devcount")
                        elif command == "2":
                            hours = int(parser.eat())
                            minutes = int(parser.eat())

                            cf.write("olderthan {} {}".format(hours, minutes))
                        elif command == "3":
                            cf.write("alive")
                        else:
                            raise InvalidOidError()

                        cf.write("\n")
                        cf.flush()

                        response = cf.readline().strip()

                        print("{}\nstring\n{}".format(self.oid, response))
                    except (TypeError, InvalidOidError):
                        pass

            connection.close()
        except ConnectionRefusedError:
            print("Connection refused. Check if meterd is running!")
            exit(os.EX_UNAVAILABLE)


class InvalidOidError(Exception):
    pass


class OidParser:
    def __init__(self, oid):
        self._oid = oid.split(".")

    def eat(self, amount=1):
        if amount < 1 or amount >= len(self._oid):
            return None

        self._oid = self._oid[amount:]
        return self._oid[0]


if __name__ == "__main__":
    MeterdQuery(sys.argv).start()
