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
import sys

from configread import configread
from functions import zabbix_send
from json import load
from pynetdevices import IPMICard
from pyzabbix import ZabbixMetric


def main():

    # set project name as current directory name
    project = os.path.abspath(__file__).split('/')[-2]

    # get config file name
    conf_file = (f'/etc/zabbix/externalscripts/{project}/{project}.conf')

    # read parameters of IPMI cards and zabbix from config file and save it to dict
    nd_parameters = configread(conf_file, 'NetworkDevice', 'device_file',
                               'login', 'password', 'printing')

    # read sensor states from config and save it to another dict
    sensor_parameters = configread(
        conf_file, 'IPMI Sensors', 'sensor_states_map_file')

    # get flag for debug printing from config
    printing = eval(nd_parameters['printing'])

    # get variables
    login = nd_parameters['login']
    password = nd_parameters['password']
    software = sys.argv[0]

    # form dictionary of matching sensor states with returned values
    with open(sensor_parameters['sensor_states_map_file'], "r") as sensor_states_map_file:
        sensor_states = load(sensor_states_map_file)

    # open file with list of monitored IPMI cards
    device_list_file = open(nd_parameters['device_file'])

    # unpack IPMI cards list to variables
    for device_line in device_list_file:
        device_type, device_name, device_ip = device_line.split(':')
        device_ip = device_ip.rstrip('\n')

        # connect to each IPMI card, get conn object
        if device_type in ('ibmc', 'ilo', 'imm'):
            device = IPMICard(device_name, device_ip, login, password)

        packet = []

        # connect to device, get sensors data and create dict of sensors values
        sensors_data = device.Connect().get_sensor_data()

        # parse sensors values and form data for send to zabbix
        for sensor_data in sensors_data:
            sensor_state = 100
            sensor_dict = {}

            # fill the dict of states with default values = 100 (Normal)
            for state_counter in range(1, 4):
                type = sensor_data.type
                name = sensor_data.name.rstrip('\x00')
                trapper_key = f'state{state_counter}[{type}.{name}]'
                sensor_dict[trapper_key] = sensor_state

            state_counter = 1

            # check that sensor return one or more states and save this states to dict
            if len(sensor_data.states):
                for sensor_data_state in sensor_data.states:
                    type = sensor_data.type
                    name = sensor_data.name.rstrip('\x00')
                    trapper_key = f'state{state_counter}[{type}.{name}]'
                    sensor_dict[trapper_key] = sensor_states.get(
                        sensor_data_state, 'Unknown')
                    state_counter += 1

            # add sensor states to packet for sending to zabbix
            for trapper_key, trapper_value in sensor_dict.items():
                packet.append(ZabbixMetric(
                    device_name, trapper_key, trapper_value))

                # print data for visual check
                if printing:
                    print(device_name)
                    print(trapper_key)
                    print(trapper_value)

            # add values if exist to packet for sending to zabbix
            if sensor_data.value:
                type = sensor_data.type
                name = sensor_data.name.rstrip('\x00')
                trapper_key = f'value[{type}.{name}]'
                trapper_value = sensor_data.value
                packet.append(ZabbixMetric(
                    device_name, trapper_key, trapper_value))

                # print data for visual check
                if printing:
                    print(device_name)
                    print(trapper_key)
                    print(trapper_value)

        # trying send data to zabbix
        zabbix_send(packet, printing, software)

    device_list_file.close()


if __name__ == "__main__":
    main()
