#!/usr/bin/env python2

from configread import configread
from pynetdevices import IPMICard
from pyslack import slack_post
from pyzabbix import ZabbixMetric, ZabbixSender
import sys

ipmi_parameters = configread('/etc/zabbix/externalscripts/pyipmizabbix/pyipmizabbix.conf',
                             'IPMICard', 'login', 'password', 'ipmicards_file',
                             'slack_hook')

ipmicards_file = open(ipmi_parameters['ipmicards_file'])

for ipmicard in ipmicards_file:
    ipmicard_params = ipmicard.split(':')
    ipmicard_type = ipmicard_params[0]
    ipmicard_name = ipmicard_params[1]
    ipmicard_ip = ipmicard_params[2]

    if ipmicard_type in ('ibmc', 'imm'):
        ipmi = IPMICard(ipmicard_name, ipmicard_ip, ipmi_parameters['login'],
                        ipmi_parameters['password'])

    sensors = {}
    sensors_list = []
    sensors_dict = {}

    sensors_descriptions = ipmi.Connect(ipmi_parameters['slack_hook']).get_sensor_descriptions()
    for sensor_description in sensors_descriptions:
        sensor_json = {"{#SENSOR_TYPE}": sensor_description['type'].strip(),
                       "{#SENSOR_NAME}": sensor_description['name'].strip()}
        sensors_list.append(sensor_json)

    sensors['data'] = sensors_list
    trapper_key = 'ipmi.sensors.discovery'
    trapper_value = str(sensors).replace("\'", "\"")
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

    sensors_descriptions = ipmi.Connect(ipmi_parameters['slack_hook']).get_sensor_descriptions()
    for sensor_description in sensors_descriptions:
        sensors_dict[sensor_description['type']] = []

    sensors_descriptions = ipmi.Connect(ipmi_parameters['slack_hook']).get_sensor_descriptions()
    for sensor_description in sensors_descriptions:
        sensor_json = {"{#SENSOR_TYPE}": sensor_description['type'].strip(),
                       "{#SENSOR_NAME}": sensor_description['name'].strip()}
        sensors_dict[sensor_description['type']].append(sensor_json)

    packet = []

    for key in sensors_dict:
        sensors['data'] = sensors_dict[key]
        trapper_key = 'ipmi.sensors.' + key.replace(" ", "").replace("/", "") + '.discovery'
        trapper_value = str(sensors).replace("\'", "\"")
        print (key)
        print (trapper_key)
        print (trapper_value)
        packet.append(ZabbixMetric(ipmicard_name, trapper_key, trapper_value))

    try:
        result = ZabbixSender(use_config=True).send(packet)
    except:
        slack_post(ipmi_parameters['slack_hook'], 'Unexpected exception in ' +
                   '\"ZabbixSender(use_config=True).send(packet)\": '
                   + str(sys.exc_info()), 'mon.forum.lo', '192.168.5.60')
        exit(1)
