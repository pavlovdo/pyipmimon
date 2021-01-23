#!/usr/bin/env python2

#
# IPMI sensors discovery for Zabbix
#
# 2016 Denis Pavlov 
#
# Discover hardware sensors from IMM/iBMC cards through IPMI and sends it to Zabbix Server via Zabbix Sender API
#
# Use with template Template IPMI Pyipmimon
#

from configread import configread
from pynetdevices import IPMICard
from pyslack import slack_post
from pyzabbix import ZabbixMetric, ZabbixSender
import sys


conf_file = ('/etc/zabbix/externalscripts/' + os.path.abspath(__file__).split('/')[-2] + '/'
                     + os.path.abspath(__file__).split('/')[-2] + '.conf')

# read parameters of IPMI cards and zabbix from config file and save it to dict
nd_parameters = configread(conf_file, 'NetworkDevice', 'device_file', 'login', 'password',
                           'zabbix_server')

# open file with list of monitored IPMI cards 
device_list_file = open(nd_parameters['device_file'])

# parse the IPMI cards list
for device_line in device_list_file:
    device_params = device_line.split(':')
    device_type = device_params[0]
    device_name = device_params[1]
    device_ip = device_params[2]

    # connect to each IPMI card, get conn object
    if device_type in ('ibmc', 'ilo', 'imm'):
        device = IPMICard(device_name, device_ip, nd_parameters['login'],
                        nd_parameters['password'])

    sensors = {}
    sensors_list = []
    sensors_dict = {}

    sensors_descriptions = device.Connect(device_parameters['slack_hook']).get_sensor_descriptions()
    for sensor_description in sensors_descriptions:
        sensor_json = {"{#SENSOR_TYPE}": sensor_description['type'].strip(),
                       "{#SENSOR_NAME}": sensor_description['name'].strip()}
        sensors_list.append(sensor_json)

    sensors['data'] = sensors_list
    trapper_key = 'ipmi.sensors.discovery'
    trapper_value = str(sensors).replace("\'", "\"")
    print (ipmicard_name)
    print (trapper_key)
    print (trapper_value)
    packet = [ZabbixMetric(ipmicard_name, trapper_key, trapper_value)]

    try:
        result = ZabbixSender(use_config=True).send(packet)
    except:
        slack_post(ipmi_parameters['slack_hook'], 'Unexpected exception in ' +
                   '\"ZabbixSender(use_config=True).send(packet)\": '
                   + str(sys.exc_info()), 'mon.forum.lo', '192.168.5.60')
        exit(1)
