#!/usr/bin/python3

import os
import sys

from pyghmi.ipmi import command
from pyghmi.exceptions import IpmiException
from functions import slack_post

# set project as current directory name, software as name of current script
project = os.path.abspath(__file__).split('/')[-2]
software = sys.argv[0]


class NetworkDevice:
    """ base class for network devices """

    def __init__(self, hostname, ip, login=None, password=None):

        self.hostname = hostname
        self.ip = ip
        self.login = login
        self.password = password


class IPMICard(NetworkDevice):
    """ class for work with IPMI cards """

    def Connect(self):

        try:
            conn = command.Command(bmc=self.ip,
                                   userid=self.login,
                                   password=self.password,
                                   verifycallback=any)
        except IpmiException as error:
            print(
                f'{project}_error: exception in {software}: can\'t connect to IPMI {self.hostname}, IP={self.ip}: {error}',
                file=sys.stderr)
            slack_post(
                software, f'can\'t connect to IPMI {self.hostname}, IP={self.ip}: {error}')
            exit(1)
        except:
            print(f'{project}_error: exception in {software}: {sys.exc_info()}',
                  file=sys.stderr)
            slack_post(software, sys.exc_info())
            exit(1)

        return conn

    def getSDRSensors(self):

        import pyghmi.ipmi.sdr

        ipmicmd = self.Connect()
        sdr = pyghmi.ipmi.sdr.SDR(ipmicmd)
        for number in sdr.get_sensor_numbers():
            rsp = ipmicmd.raw_command(command=0x2d, netfn=4, data=(number,))
            if 'error' in rsp:
                continue
            reading = sdr.sensors[number].decode_sensor_reading(rsp['data'])
            if reading is not None:
                print(repr(reading))

    def PrintAttrs(self):
        print(self.hostname)
        print(self.login)
        print(self.password)
