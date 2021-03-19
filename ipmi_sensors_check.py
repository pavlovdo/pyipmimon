#!/usr/bin/python3

#
# IPMI sensors values check
#
# 2020 Denis Pavlov
#

import os

from configread import configread
from pynetdevices import IPMICard


def main():

    # set project name as current directory name
    project = os.path.abspath(__file__).split('/')[-2]

    # get config file name
    conf_file = (f'/etc/zabbix/externalscripts/{project}/{project}.conf')

    # read parameters of IPMI cards and zabbix from config file and save it to dict
    nd_parameters = configread(conf_file, 'NetworkDevice', 'device_file',
                               'login', 'password', 'printing')

    # get variables
    login = nd_parameters['login']
    password = nd_parameters['password']

    # open file with list of monitored IPMI cards
    device_list_file = open(nd_parameters['device_file'])

    device_type, device_name, device_ip = device_list_file.readline().split(':')
    device_ip = device_ip.rstrip('\n')

    # connect to first IPMI card, get conn object
    if device_type in ('ibmc', 'ilo', 'imm'):
        device = IPMICard(device_name, device_ip, login, password)

    # connect to device, get sensors data and create dict of sensors values
    sensors_data = device.Connect().get_sensor_data()

    # parse sensors values and form data for send to zabbix
    for sensor_data in sensors_data:
        print(f'type: {sensor_data.type}, name: {sensor_data.name}, '
              f'health: {sensor_data.health}, states: {sensor_data.states}, '
              f'state_ids: {sensor_data.state_ids}, imprecision={sensor_data.imprecision}')

    device_list_file.close()


if __name__ == "__main__":
    main()
