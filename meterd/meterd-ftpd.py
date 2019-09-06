#!/usr/local/meterd/venv/bin/python3

# This script is intended to be started through a systemd timer
# Florian Buehrle 2019

import os
import lib.yaml as yaml
import fcntl
import time
import logging
from lib.yaml.loader import Loader
from ftplib import FTP, error_perm
from socket import gaierror, timeout
from datetime import datetime
from handlers import SystemdHandler


class MeterdFtpd:
    def __init__(self):
        self.masterpath = "/etc/meterd/"

        self.server = ""
        self.wdir = ""
        self.fname = ""
        self.user = ""
        self.passw = ""
        self.xmlpath = ""

        try:
            with open(self.masterpath + "main.yaml", 'r') as maincfg:
                cfg = yaml.load(maincfg, Loader=Loader)

                cfg_ftp = cfg["ftp"]
                cfg_main = cfg["main"]

                self.server = cfg_ftp["server"]
                self.wdir = cfg_ftp["wdir"]
                self.fname = cfg_ftp["fname"]
                self.user = cfg_ftp["user"]
                self.passw = cfg_ftp["pass"]
                self.xmlpath = cfg_main["xmlpath"]
        except FileNotFoundError:
            logging.error("Main config file not found.")
            exit(os.EX_CONFIG)
        except KeyError:
            logging.error("Invalid main config file.")
            exit(os.EX_CONFIG)

    def run(self):
        try:
            now = datetime.utcnow()
            formatted_fname = now.strftime(self.fname)

            logging.info("Connecting to {}/{}.".format(self.server, self.wdir))

            with FTP(self.server, timeout=5) as ftp:
                ftp.login(self.user, self.passw)
                ftp.cwd(self.wdir)

                while True:
                    with open(self.xmlpath, 'br+') as xmlfile:
                        try:
                            fcntl.flock(xmlfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        except BlockingIOError:
                            logging.warning("The XML file is locked. Retrying in 1s...")
                            time.sleep(1)
                            continue

                        logging.info("Pushing file {} as {}.".format(self.xmlpath, formatted_fname))

                        ftp.storbinary("STOR " + formatted_fname, xmlfile)

                        xmlfile.seek(0)
                        xmlfile.truncate()

                        fcntl.flock(xmlfile, fcntl.LOCK_UN)

                        logging.info("Success.")
                        break
        except error_perm as e:
            if str(e).startswith("550"):
                logging.error("Working directory {} does not exist.".format(self.wdir))
            else:
                logging.error("Login failed.")
            exit(os.EX_NOPERM)
        except (gaierror, timeout):
            logging.error("Couldn't reach server " + self.server)
            exit(os.EX_UNAVAILABLE)
        except FileNotFoundError:
            logging.error("File {} does not exist. Is the main daemon running?".format(self.xmlpath))
            exit(os.EX_NOINPUT)
        except (IOError, PermissionError):
            logging.error("Could not open file {} in RW-mode. Check permissions!".format(self.xmlpath))
            exit(os.EX_NOPERM)


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel("INFO")
    logger.addHandler(SystemdHandler())

    MeterdFtpd().run()
