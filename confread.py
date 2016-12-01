#!/usr/bin/env python3

import configparser


def configread(conffile, section, *parameters):

    # Read the Orbit configuration file
    config = configparser.RawConfigParser()
    config.read(conffile)
    params = dict()

    for parameter in parameters:
        try:
            params[parameter] = config.get(section, parameter)
        except configparser.NoOptionError as err:
            print (err, '. Please set ' + parameter + ' value in the ' +
                   'configuration file ' + conffile)

    return params
