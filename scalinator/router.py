#!/usr/bin/env python
"""
router : Retrieves OCP router/HAProxy stats, extracts BE rate metric
Author(s): Julian Gericke (julian@lsd.co.za)
(c) LSD Information Technology
http://www.lsd.co.za
"""
import json
import re
import logging
from haproxystats import HAProxyServer

logger = logging.getLogger(__name__)

class Router(object):

    def __init__(self, router_uri, router_user, router_passwd):
        self.uri = router_uri
        # Nasty URI to FQDN conversion
        self.fqdn = re.sub(r'(http.*://)|(:.*)', "", self.uri)
        self.user = router_user
        self.passwd = router_passwd

    def RetrStats(self):
        '''
        Retrieve router stats
        '''
        try:
            router_stats = HAProxyServer(
                self.fqdn, self.user, self.passwd, False)
            return(json.loads(router_stats.to_json()))
        except Exception as error:
            logging.error(error)
            raise

    def RetrBackendRate(self, router_stats, router_backend):
        '''
        Retrieve backend rate metric:
        rate: number of sessions per second over last elapsed second
        '''    
        try:
            router_backend_stats = list(filter(lambda backend_stats: backend_stats[
                                        'name'] == router_backend, router_stats[self.fqdn]['backends']))
            if router_backend_stats and 'rate' in router_backend_stats[0]:
                return(router_backend_stats[0]['rate'])
        except Exception as error:
            logging.error(error)
            raise