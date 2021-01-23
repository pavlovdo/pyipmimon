#!/usr/bin/python3

#
# IPMI sensors discovery for Zabbix
#
# 2016-2021 Denis Pavlov
#
# Discover hardware sensors from IMM/iBMC cards through IPMI and sends it to Zabbix Server via Zabbix Sender API
#
# Use with template Template IPMI Pyipmimon
#

import os
import socket

from collections import defaultdict
from configread import configread
from pynetdevices import IPMICard
from pyslack import slack_post
from pyzabbix import ZabbixMetric, ZabbixSender


# set config file name
conf_file = '/etc/zabbix/externalscripts/pyipmimon/conf.d/pyipmimon.conf'

# read network device parameters from config and save it to dict
nd_parameters = configread(conf_file, 'NetworkDevice', 'device_file',
                           'login', 'password', 'slack_hook',
                           'zabbix_server', 'printing')

# get flag for debug printing from config
printing = eval(nd_parameters['printing'])

# open file with list of monitored IPMI cards
device_list_file = open(nd_parameters['device_file'])

# separate discoveries in zabbix template
special_discoveries = ['Cable/Interconnect', 'Cooling Device', 'Current',
                       'Drive Bay', 'Fan', 'Power Supply', 'Temperature',
                       'Voltage']

# parse the IPMI cards list
for device_line in device_list_file:
    device_params = device_line.split(':')
    device_type = device_params[0]
    device_name = device_params[1]
    device_ip = device_params[2].strip('\n')

    # connect to each IPMI card, get conn object
    if device_type in ('ibmc', 'ilo', 'imm'):
        device = IPMICard(device_name, device_ip, nd_parameters['slack_hook'],
                          nd_parameters['login'],
                          nd_parameters['password'])

    sensors = {}
    sensors_list = []

    # create dictionary of types of sensors
    sensors_dict = defaultdict(list)

    # get sensors and create common list of sensors types and names in JSON
    sensors_descriptions = device.Connect().get_sensor_descriptions()
    for sensor_description in sensors_descriptions:
        sensor_json = {"{#SENSOR_TYPE}": sensor_description['type'].strip(),
                       "{#SENSOR_NAME}": sensor_description['name'].rstrip()}
        if sensor_description['type'] not in special_discoveries:
            sensors_list.append(sensor_json)
        # form dictionary of types of sensors
        sensors_dict[sensor_description['type']].append(sensor_json)

    # form data for send to zabbix
    sensors['data'] = sensors_list
    trapper_key = 'ipmi.sensors.discovery'
    trapper_value = str(sensors).replace("\'", "\"")

    # form list of data with common discovery for sending to zabbix
    packet = [ZabbixMetric(device_name, trapper_key, trapper_value)]

    # print data for visual check
    if printing:
        print(device_name)
        print(trapper_key)
        print(trapper_value)

    # form list of data with individual discoveries for sending to zabbix
    for sensor_type in sensors_dict:
        sensors['data'] = sensors_dict[sensor_type]
        trapper_key = 'ipmi.sensors.' + \
            sensor_type.replace(" ", "").replace("/", "") + '.discovery'
        trapper_value = str(sensors).replace("\'", "\"")

        # add individual discoveries to list of data for sending to zabbix
        packet.append(ZabbixMetric(device_name, trapper_key, trapper_value))

        # print data for visual check
        if printing:
            print(device_name)
            print(trapper_key)
            print(trapper_value)

    # trying send data to zabbix
    try:
        result = ZabbixSender(nd_parameters['zabbix_server']).send(packet)
    except ConnectionRefusedError as error:
        slack_post(nd_parameters['slack_hook'],
                   f"Unexpected exception in \"ZabbixSender({nd_parameters['zabbix_server']}.send(packet)\": {str(error)}",
                   nd_parameters['zabbix_server'],
                   socket.gethostbyname(nd_parameters['zabbix_server'])
                   )
        exit(1)
