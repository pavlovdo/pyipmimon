Description
===========
Zabbix physical server sensors monitoring via IPMI

Tested with IBM x3550/x3755, Lenovo SR570/SR630


Requirements
============

1) python >= 3.6

2) python module pyghmi: connect and get information from iBMC/IMM server cards via IPMI

3) zabbix-server (tested with versions 4.4-5.2)

4) python module py-zabbix: sending traps to zabbix


Installation
============
1) Give access to servers hardware (IMM/iBMC etc.) for monitoring user with permissions to Remote Console Access.

2) Clone pyipmimon repo to directory /etc/zabbix/externalscripts of monitoring server:
```
sudo mkdir -p /etc/zabbix/externalscripts
cd /etc/zabbix/externalscripts
sudo git clone https://github.com/pavlovdo/pyipmimon
```

3) A) Check execute permissions for scripts:
```
ls -l *.py *.sh
```
B) If not:
```
sudo chmod +x *.py *.sh
```

4) Change example configuration file pyipmimon.conf: login, password, address of zabbix_server;

5) Change example configuration file devices.conf: IP and zabbix names of IPMI cards;

6) Give and check network access from monitoring server to IPMI cards management network port (UDP/623);

7) Check configuration and running zabbix trappers on your zabbix server or proxy:
```
### Option: StartTrappers
#       Number of pre-forked instances of trappers.
#       Trappers accept incoming connections from Zabbix sender, active agents and active proxies.
#       At least one trapper process must be running to display server availability and view queue
#       in the frontend.
#
# Mandatory: no
# Range: 0-1000
# Default:
# StartTrappers=5
```
```
# ps aux | grep trapper
zabbix    776389  0.2  0.4 2049416 111772 ?      S    дек07  63:41 /usr/sbin/zabbix_server: trapper #1 [processed data in 0.000166 sec, waiting for connection]
zabbix    776390  0.2  0.4 2049512 112016 ?      S    дек07  63:43 /usr/sbin/zabbix_server: trapper #2 [processed data in 0.000342 sec, waiting for connection]
zabbix    776391  0.2  0.4 2049452 112092 ?      S    дек07  63:12 /usr/sbin/zabbix_server: trapper #3 [processed data in 0.000301 sec, waiting for connection]
zabbix    776392  0.2  0.4 2049600 112064 ?      S    дек07  63:57 /usr/sbin/zabbix_server: trapper #4 [processed data in 0.000187 sec, waiting for connection]
zabbix    776393  0.2  0.4 2049412 111836 ?      S    дек07  63:31 /usr/sbin/zabbix_server: trapper #5 [processed data in 0.000176 sec, waiting for connection]
```

8) Import template Chassis by IPMI Pyipmimon.json to Zabbix, if use Zabbix 5.2,
and Template IPMI Pyipmimon.xml (no more support) for Zabbix 4.4;

9) Create your IPMI cards hosts in Zabbix and link this template to them.
In host configuration set parameters "Host name" and "IP address" for Agent Interface.
Use the same hostname as in the file devices.conf, server1_imm for example.

10) Further you have options: run scripts from host or run scripts from docker container.

If you want to run scripts from host:

A) Install Python 3 and pip3 if it is not installed;

B) Install required python modules:
```
pip3 install -r requirements.txt
```

C) Create cron jobs for zabbix trappers:
```
echo "00 */1 * * *  /etc/zabbix/externalscripts/pyipmimon/ipmi_sensors_discovery.py" > /tmp/crontab && \
echo "*/1 * * * *   /etc/zabbix/externalscripts/pyipmimon/ipmi_sensors_trappers.py" >> /tmp/crontab && \
crontab /tmp/crontab && rm /tmp/crontab
```

If you want to run scripts from docker container:

A) Run build.sh:
```
cd /etc/zabbix/externalscripts/pyipmimon
./build.sh
```

B) Run dockerrun.sh;
```
./dockerrun.sh
```


Notes
======
1) For send exception alarms via slack hook to your slack channel, set parameter slack_hook in conf.d/pyipmimon.conf.
More details in https://api.slack.com/messaging/webhooks


Related Links
=============
http://www.intel.com/content/www/us/en/servers/ipmi/ipmi-technical-resources.html

https://pypi.org/project/pyghmi/

https://opendev.org/x/pyghmi

https://github.com/adubkov/py-zabbix
