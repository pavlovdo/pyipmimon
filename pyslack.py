#!/usr/bin/env python3

import requests


def slack_post(slack_hook, message, hostname, ip, icon_emoji=':snake:'):

    import os
    import sys

    requests.post(slack_hook, json={'username': os.uname()[1],
                                    'icon_emoji': icon_emoji,
                                    'text': 'ERROR in: \"' +
                                    str(sys.argv[0]) + ', ' + hostname + ', '
                                    + ip + '\"\n' +
                                    message})
