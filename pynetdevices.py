#!/usr/bin/env python3


class NetworkDevice:
    """ base class for network devices """

    def __init__(self, hostname, ip, login=None, password=None, enablepw=None,
                 slack_hook=None):

        self.hostname = hostname
        self.ip = ip
        self.login = login
        self.password = password
        self.enablepw = enablepw
        self.slack_hook = slack_hook


class IPMICard(NetworkDevice):
    """ class for IPMI cards """

    def Connect(self, slack_hook):

        import pyghmi.ipmi.command
        from pyslack import slack_post
        import sys

        try:
            connect = pyghmi.ipmi.command.Command(bmc=self.ip,
                                                  userid=self.login,
                                                  password=self.password)
        except pyghmi.exceptions.IpmiException as error_name:
            slack_post(slack_hook, 'Can\'t connect to the IPMI: '
                       + str(error_name), self.hostname, self.ip)
            exit(1)
        except:
            slack_post(slack_hook, 'Unexpected exception in ' +
                       '\"imm.Connect().get_sensor_descriptions()\": '
                       + str(sys.exc_info()), self.hostname, self.ip)
            exit(1)

        return connect

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
        print(self.host)
        print(self.login)
        print(self.password)
