#!/usr/bin/python3

#
# IPMI sensors values monitoring for Zabbix
#
# 2016-2020 Denis Pavlov
#
# Discover hardware sensors values from IMM/iBMC cards through IPMI and sends it to Zabbix Server via Zabbix Sender API
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

# parse the IPMI cards list
for device_line in device_list_file:
    device_params = device_line.split(':')
    device_type = device_params[0]
    device_name = device_params[1]
    device_ip = device_params[2].strip('\n')

    # connect to each IPMI card, get conn object
    if device_type in ('ibmc', 'ilo', 'imm'):
        device = IPMICard(device_name, device_ip, nd_parameters['slack_hook'],
                          nd_parameters['login'], nd_parameters['password'])

    # dict of sensor states
    sensor_states = {
        "Absent": 0,
        "Present": 1,
        "Ok": 2,
        "Redundant": 3,
        "Not redundant": 4,
        "Power input lost": 5,
        "Connected": 6,
        "Deasserted": 7,
        "Predictive failure deasserted": 8,
        "Successful software/firmware change": 9,
        "Event log full": 10,
        "Event log nearly full": 11,
        "lower critical threshold": 12,
        "Progress": 13,
        "Asserted": 14,
        "Power off": 15,
        "Predictive drive failure": 16,
        "Drive in critical array": 17,
        "Drive fault": 18,
        "Rebuild in progress": 19,
        "Log clear": 20,
        "No bootable media": 21,
        "Correctable memory error logging limit reached": 22,
        "Memory Logging Limit Reached": 23,
        "Slot/connector installed": 24,
        "Spare": 25,
        "Chassis intrusion": 26,
        "Bus uncorrectable error": 27,
        "Uncorrectable error": 28,
        "Device disabled": 29,
        "Scrub failed": 30,
        "Non-Critical": 31,
    }

    packet = []

    # # connect to device, get sensors data and create dict of sensors values
    sensors_data = device.Connect().get_sensor_data()

    # parse sensors values and form data for send to zabbix
    for sensor_data in sensors_data:
        sensor_state = 100
        sensor_dict = {}
        for state_counter in range(1, 6):
            trapper_value = sensor_state
            trapper_key = 'state' + \
                str(state_counter) + '[' + sensor_data.type + \
                '.' + sensor_data.name.rstrip('\x00') + ']'
            sensor_dict[trapper_key] = trapper_value
        state_counter = 1
        if len(sensor_data.states):
            # add sensors states for sending to zabbix
            for sensor_data_state in sensor_data.states:
                trapper_value = sensor_states[sensor_data_state]
                trapper_key = 'state' + \
                    str(state_counter) + '[' + sensor_data.type + \
                    '.' + sensor_data.name.rstrip('\x00') + ']'
                sensor_dict[trapper_key] = trapper_value
                state_counter += 1

        for trapper_key in sensor_dict:
            packet.append(ZabbixMetric(
                device_name, trapper_key, sensor_dict[trapper_key]))

            # print data for visual check
            if printing:
                print(device_name)
                print(trapper_key)
                print(sensor_dict[trapper_key])

        # add values if exist for sending to zabbix
        if sensor_data.value:
            trapper_key = 'value' + \
                '[' + sensor_data.type + '.' + \
                sensor_data.name.rstrip('\x00') + ']'
            trapper_value = sensor_data.value
            packet.append(ZabbixMetric(
                device_name, trapper_key, trapper_value))

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
