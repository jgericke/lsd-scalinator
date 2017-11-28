"""Scalinator : rate based pod autoscaling within Red Hat OpenShift."""
# !/usr/bin/env/python
# Author(s): Julian Gericke <julian@lsd.co.za>
# (c) LSD Information Technology
# http://www.lsd.co.za
import json
import requests
import logging

logger = logging.getLogger(__name__)


def rocket_notify(rocket_webhook_url, rocket_msg):
    '''WebHook notify (RocketChat)'''

    try:
        rocket_msg = {'text': rocket_msg}
        requests.post(rocket_webhook_url,
                      data=json.dumps(rocket_msg),
                      headers={'Content-type': 'application/json'},
                      verify=False)
    except requests.exceptions.RequestException as error:
        logger.error(error)
