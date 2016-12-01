#!/usr/bin/env python2

import ConfigParser


def configread(conffile, section, *parameters):

    # Read the Orbit configuration file
    config = ConfigParser.RawConfigParser()
    config.read(conffile)
    params = dict()

    for parameter in parameters:
        try:
            params[parameter] = config.get(section, parameter)
        except ConfigParser.NoOptionError as err:
            print (err, '. Please set ' + parameter + ' value in the ' +
                   'configuration file ' + conffile)

    return params
