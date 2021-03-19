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
import sys

from collections import defaultdict
from configread import configread
from functions import zabbix_send
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

    # get flag for debug printing from config
    printing = eval(nd_parameters['printing'])

    special_discoveries = ['Cable/Interconnect', 'Cooling Device', 'Current',
                           'Drive Bay', 'Fan', 'Power Supply', 'Temperature',
                           'Voltage']

    # get variables
    login = nd_parameters['login']
    password = nd_parameters['password']
    software = sys.argv[0]

    # open file with list of monitored IPMI cards
    device_list_file = open(nd_parameters['device_file'])

    # unpack IPMI cards list to variables
    for device_line in device_list_file:
        device_type, device_name, device_ip = device_line.split(':')
        device_ip = device_ip.rstrip('\n')

        # connect to each IPMI card, get conn object
        if device_type in ('ibmc', 'ilo', 'imm'):
            device = IPMICard(device_name, device_ip, login, password)

        sensors = {}
        common_sensors_list = []

        # create dictionary of types of sensors
        special_sensors_dict = defaultdict(list)

        # get sensors and create list of common sensors and dictionary of special sensors
        sensors_descriptions = device.Connect().get_sensor_descriptions()
        for sensor_description in sensors_descriptions:
            sensor_type = sensor_description['type'].strip()
            sensor_name = sensor_description['name'].rstrip()
            sensor_json = {"{#TYPE}": sensor_type, "{#NAME}": sensor_name}
            if sensor_type in special_discoveries:
                special_sensors_dict[sensor_type].append(sensor_json)
            else:
                common_sensors_list.append(sensor_json)

        # form common sensors discovery for sending to zabbix
        sensors['data'] = common_sensors_list
        trapper_key = 'ipmi.sensors.discovery'
        trapper_value = str(sensors).replace("\'", "\"")

        # print common sensors discovery for visual check
        if printing:
            print(device_name)
            print(trapper_key)
            for sensor in common_sensors_list:
                print(sensor)

        # form list of data with common sensors discovery for sending to zabbix
        packet = [ZabbixMetric(device_name, trapper_key, trapper_value)]

        # form data with separate special discoveries for sending to zabbix
        for sensor_type in special_sensors_dict:
            sensors['data'] = special_sensors_dict[sensor_type]
            type = sensor_type.replace(" ", "").replace("/", "")
            trapper_key = f'ipmi.sensors.{type}.discovery'
            trapper_value = str(sensors).replace("\'", "\"")

            # add special discoveries to list of data for sending to zabbix
            packet.append(ZabbixMetric(
                device_name, trapper_key, trapper_value))

            # print data for visual check
            if printing:
                print(device_name)
                print(trapper_key)
                for sensor in sensors['data']:
                    print(sensor)

        # trying send data to zabbix
        zabbix_send(packet, printing, software)

    device_list_file.close()


if __name__ == "__main__":
    main()
