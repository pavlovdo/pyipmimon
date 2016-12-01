#!/usr/bin/env python2


class NetworkDevice:

    def __init__(self, hostname, ip, login=None, password=None, enablepw=None):

        self.hostname = hostname
        self.ip = ip
        self.login = login
        self.password = password
        self.enablepw = enablepw


class CiscoDevice(NetworkDevice):

    def getConfig(self, printing=False):

        import paramiko

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(self.ip.rstrip(), username=self.login,
                       password=self.password, timeout=10,
                       allow_agent=False, look_for_keys=False)
        stdin, stdout, stderr = client.exec_command('show run')
        confbinary = stdout.read() + stderr.read()

        conftext = confbinary.decode("utf-8")
        conflist = conftext.split("\n")[4:]

        if printing:
            for confline in conflist:
                print (confline)

        client.close()

        return conflist

    def saveConfig(self, conflist, savedir):

        fh = open(savedir + '/' + self.hostname, 'w')
        for confline in conflist:
            fh.write(confline + '\n')
        fh.close()


class CiscoASA(CiscoDevice):

    def getConfig(self, endstring=': end', printing=False):

        import paramiko

        conffull = ''
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(self.ip.rstrip(), username=self.login,
                       password=self.password, allow_agent=False,
                       look_for_keys=False)

        channel = client.invoke_shell()
        channel.send('enable\n')
        channel.send(self.enablepw + '\n')

        while True:
            channel.send('show run\n')
            confbinary = channel.recv(4096)
            conftext = confbinary.decode("utf-8")
            if endstring in conftext:
                endindex = conftext.find(endstring)
                conffull += conftext[:endindex]
                break
            conffull += conftext

        conflist = conffull.split("\n")[4:]

        if printing:
            for confline in conflist:
                print (confline)

        channel.close()
        client.close()

        return conflist


class CiscoNexus(CiscoDevice):
    pass


class CiscoRouter(CiscoDevice):
    pass


class CiscoSwitch(CiscoDevice):
    pass


class IPMICard(NetworkDevice):

    def Connect(self, slack_hook):

        import pyghmi.ipmi.command
        from pyslack import slack_post
        import sys

        try:
            connect = pyghmi.ipmi.command.Command(bmc=self.ip,
                                                  userid=self.login,
                                                  password=self.password,
                                                  onlogon=None, kg=None)
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
                print (repr(reading))

    def PrintAttrs(self):
        print (self.host)
        print (self.login)
        print (self.password)


class LinuxServer(NetworkDevice):

    def getConfig(self, remotepath, tempdir='./tmp/',
                  use_key_pairs=True, printing=False):

        import os
        import paramiko

        self.tempdir = tempdir

        client = paramiko.SSHClient()
        client.load_system_host_keys()

        if use_key_pairs:
            client.connect(self.hostname)
        else:
            client.connect(self.hostname, username=self.login,
                           password=self.password)

        temppath = tempdir + os.path.basename(remotepath)
        sftp = client.open_sftp()
        sftp.get(remotepath, temppath)

        if printing:
            fhand = open(temppath, 'r')
            for line in fhand:
                print(line)

    def saveConfig(self, filename, savedir='./data', overwrite=True, vc=True):

        import os

        if not os.path.exists(savedir + '/' + self.hostname):
            os.mkdir(savedir + '/' + self.hostname)

        dstpath = savedir + '/' + self.hostname + '/' + filename
        if not os.path.isfile(dstpath) or overwrite:
            os.rename(self.tempdir + filename, dstpath)
        else:
            print ('File ' + dstpath + ' is already exist, keep the old file')
