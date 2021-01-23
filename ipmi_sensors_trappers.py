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

    if ipmicard_type in ('ibmc', 'ilo', 'imm'):
        ipmi = IPMICard(ipmicard_name, ipmicard_ip, ipmi_parameters['login'],
                        ipmi_parameters['password'])
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
    }

    packet = []

    sensors_data = ipmi.Connect(ipmi_parameters['slack_hook']).get_sensor_data()
    for sensor_data in sensors_data:
        sensor_state = 0
        for sensor_data_state in sensor_data.states:
            sensor_state |= sensor_states[sensor_data_state]
        trapper_key = 'state' + '[' + sensor_data.type + '.' + sensor_data.name + ']'
        trapper_value = sensor_state
        print ipmicard_name
        print trapper_key
        print trapper_value
        packet.append(ZabbixMetric(ipmicard_name, trapper_key, trapper_value))

        if sensor_data.value:
            trapper_key = 'value.' + sensor_data.type.replace(" ", "").replace("/", "") + '[' + sensor_data.name + ']'
            trapper_value = sensor_data.value
            packet.append(ZabbixMetric(ipmicard_name, trapper_key, trapper_value))

    try:
        result = ZabbixSender(use_config=True).send(packet)
    except:
        slack_post(ipmi_parameters['slack_hook'], 'Unexpected exception in ' +
                   '\"ZabbixSender(use_config=True).send(packet)\": '
                   + str(sys.exc_info()), 'mon.forum.lo', '192.168.5.60')
        exit(1)
