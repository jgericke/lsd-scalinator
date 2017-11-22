#!/usr/bin/env python
"""
scalinator : Demonstrating rate based pod autoscaling within Red Hat OpenShift
Author(s): Julian Gericke (julian@lsd.co.za)
(c) LSD Information Technology
http://www.lsd.co.za
"""
import os
import sys
import time
import logging
import requests
import json
import asyncio
import biome
from openshift import OpenShift
from router import Router
from notify import rocket_notify
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

try: 
    if hasattr(biome.SCALINATOR, 'loglevel'):
        logging.basicConfig(stream=sys.stdout, level=biome.SCALINATOR.loglevel,
                            format='%(asctime)s %(name)s %(levelname)s %(message)s')
    else:
        logging.basicConfig(stream=sys.stdout, level='INFO',
                            format='%(asctime)s %(name)s %(levelname)s %(message)s')
    logger = logging.getLogger(__name__)
except (KeyError, ValueError, AttributeError, Exception) as error:
    raise
     

class Scalinator(object):
    def __init__(self, scalinator_name, scalinator_poll_interval, scalinator_scale_interval, scalinator_sample_time, scalinator_sample_length, scalinator_router_backend, scalinator_openshift_namespace, scalinator_openshift_deploymentconfig):
        self.name = scalinator_name
        self.poll_interval = scalinator_poll_interval
        self.scale_interval = scalinator_scale_interval
        self.sample_time = scalinator_sample_time
        self.sample_length = scalinator_sample_length
        self.router_backend = scalinator_router_backend
        self.openshift_namespace = scalinator_openshift_namespace
        self.openshift_deploymentconfig = scalinator_openshift_deploymentconfig
        self.rate_aggr = []
        self.replicas = 0
   
    def ScaleArbiter(self, avg_rate):
        '''
        Scaling on pre-calculated thresholds is kinda weak...
        - Ideally this would be a moving average based decision
        - Ideally-ier additional metrics such as req_rate, rtime and scur would be factored in
        Lastly, yuck!
        '''
        # Caters to 0 active load generator/minimal traffic
        if avg_rate >= 0 and avg_rate <= 9:
            return(1)
        # Caters to 1 active load generators/modest traffic
        if avg_rate >= 10 and avg_rate <= 29:
            return(2)
        # Caters to 2+ active load generators/decent traffic
        if avg_rate >= 30:
            return(3)         


async def poll(scaler, router, openshift):
    while True:
        for rate_sample_count in range(scaler.sample_time):    
            '''
            Poll router stats
            '''
            router_stats = Router.RetrStats(router)
            '''
            Extract rate (sessions p/s over the last second)
            from polled router_stats
            '''
            router_be_rate = Router.RetrBackendRate(router, router_stats, scaler.router_backend)
            '''
            Confirm we have a rate to work with
            '''
            if isinstance(router_be_rate, int):
                '''
                Append to our rate aggregation
                '''
                scaler.rate_aggr.append(router_be_rate)
                logging.debug('{} current rate {} aggregated rates {}'.format(scaler.name, router_be_rate, scaler.rate_aggr))
                await asyncio.sleep(scaler.poll_interval)       
            else:
                logging.warn('{} retrieved an invalid router_be_rate'.format(
                    scaler.name))
        await scale(scaler, openshift)
            

async def scale(scaler, openshift):
        '''
        If aggregated rates are in excess of the defined sample length
        purge oldest rate aggregation
        '''
        if len(scaler.rate_aggr) > scaler.sample_length:
            del scaler.rate_aggr[0:scaler.sample_time]
            logger.debug('{} purged rate_aggr {}'.format(scaler.name, scaler.rate_aggr))
        '''
        Calculate an average against aggregated
        rates
        '''    
        avg_rate = int(
            round(sum(scaler.rate_aggr) / float(len(scaler.rate_aggr))))                
        '''
        Retrieve number of applicable replicas based on averaged rate
        '''
        replica_target = scaler.ScaleArbiter(avg_rate)
        logging.debug('{} replica_target {} avg_rate {}'.format(
            scaler.name, replica_target, avg_rate))
        '''
        Confirm OpenShift oauth2 token validity and re-auth if required
        '''
        if not openshift.ValidateToken():
            openshift.Auth()        
        ''' 
        Retrieve current replicas
        '''
        scaler.replicas = openshift.RetrReplicas(scaler.openshift_namespace, scaler.openshift_deploymentconfig)
        logging.debug('{} current replicas {}'.format(scaler.name, scaler.replicas))
        '''
        Determined current to desired replicas
        '''
        if(replica_target > scaler.replicas) or (replica_target < scaler.replicas):
            logging.info('{} scaling {} from {} to {} rate average {}'.format(
                scaler.name, scaler.openshift_deploymentconfig, scaler.replicas, replica_target, avg_rate))
            '''
            Scale out/in based on retrieved scale rate and update
            current replicas
            '''
            openshift.SetReplicas(scaler.openshift_namespace, scaler.openshift_deploymentconfig, replica_target)
            scaler.replicas = replica_target
            logging.info('{} scaled {} replicas {}'.format(
                scaler.name, scaler.openshift_deploymentconfig, scaler.replicas))
            '''
            Cooling period before we continue polling
            '''
            await asyncio.sleep(scaler.scale_interval)


if __name__ == "__main__":
    try:
        scalers = []
        router = Router(biome.ROUTER.uri, biome.ROUTER.user, biome.ROUTER.passwd)
        openshift = OpenShift(biome.OPENSHIFT.uri, biome.OPENSHIFT.user, biome.OPENSHIFT.passwd)
        for cfg in range(len(biome.SCALINATOR.get_dict('config')['scalers'])):
            scalers.append(Scalinator(
                biome.SCALINATOR.get_dict('config')['scalers'][cfg]['name'], 
                biome.SCALINATOR.get_dict('config')['scalers'][cfg]['poll_interval'], 
                biome.SCALINATOR.get_dict('config')['scalers'][cfg]['scale_interval'],
                biome.SCALINATOR.get_dict('config')['scalers'][cfg]['sample_time'], 
                biome.SCALINATOR.get_dict('config')['scalers'][cfg]['sample_length'],
                biome.SCALINATOR.get_dict('config')['scalers'][cfg]['router_backend'],
                biome.SCALINATOR.get_dict('config')['scalers'][cfg]['openshift_namespace'],
                biome.SCALINATOR.get_dict('config')['scalers'][cfg]['openshift_deploymentconfig']))
        try:
            ioloop = asyncio.get_event_loop()
            for scaler in scalers:
                tasks = [
                    ioloop.create_task(poll(scaler, router, openshift)),
                ]        
            ioloop.run_until_complete(asyncio.wait(tasks))
        except KeyboardInterrupt:
            pass
        finally:
            ioloop.close()
    except (KeyError, ValueError, AttributeError, TypeError) as env_error:
        logging.error(env_error)        
        raise
    except Exception as error:
        logging.error(error)
        raise
