"""Scalinator : rate based pod autoscaling within Red Hat OpenShift."""
# !/usr/bin/env/python
# Author(s): Julian Gericke <julian@lsd.co.za>
# (c) LSD Information Technology
# http://www.lsd.co.za
import json
import re
import logging
from haproxystats import HAProxyServer

logger = logging.getLogger(__name__)


class Router(object):
    """Router: Retrieve HAProxy statistics."""

    def __init__(self, router_uri, router_user, router_passwd):
        self.uri = router_uri
        # Nasty URI to cannonical name conversion
        self.fqdn = re.sub(r'(http.*://)|(:.*)', "", self.uri)
        self.user = router_user
        self.passwd = router_passwd

    def RetrStats(self):
        '''
        Retrieve router stats
        '''
        try:
            self.stats = json.loads(HAProxyServer(
                self.fqdn, self.user, self.passwd, False).to_json())
        except Exception as error:
            logging.error(error)
            raise

    def RetrBackendRate(self, router_backend):
        '''
        Retrieve backend rate metric:
        rate: number of sessions per second over last elapsed second
        '''
        try:
            router_backend_rate = list(filter(lambda backend_stats: backend_stats['name'] == router_backend, self.stats[self.fqdn]['backends']))
            if router_backend_rate and 'rate' in router_backend_rate[0]:
                return(router_backend_rate[0]['rate'])
        except Exception as error:
            logging.error(error)
            raise
