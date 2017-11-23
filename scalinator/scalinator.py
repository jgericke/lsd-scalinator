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
import json
import asyncio
import biome
from openshift import OpenShift
from router import Router
from notify import rocket_notify


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
        self.current_replicas = 0


    def ScaleAggregator(self, be_rate):
        '''
        Test we have a valid BE rate to work with
        '''
        if isinstance(be_rate, int):
            '''
            Append to scaler's rate aggregation
            '''
            self.rate_aggr.append(be_rate)        
        else:
            logging.warn('{} retrieved an invalid be_rate'.format(
                self.name))


    def ScaleMedian(self):
        '''
        If aggregated rates are in excess of the defined sample length
        purge oldest rate aggregation
        '''
        if len(self.rate_aggr) > self.sample_length:
            del self.rate_aggr[0:self.sample_time]
        '''
        Average rate for rate aggregation (rate_aggr)
        '''    
        self.avg_rate = int(
            round(sum(self.rate_aggr) / float(len(self.rate_aggr))))      

   
    def ScaleArbiter(self):
        '''
        Scaling on pre-calculated thresholds is kinda weak...
        - Ideally this would be a moving average based decision
        - Ideally-ier additional metrics such as req_rate, rtime and scur would be factored in
        Lastly, yuck!
        '''
        # Caters to 0 active load generator/minimal traffic
        if self.avg_rate >= 0 and self.avg_rate <= 9:
            self.target_replicas = 1
        # Caters to 1 active load generators/modest traffic
        if self.avg_rate >= 10 and self.avg_rate <= 29:
            self.target_replicas = 2
        # Caters to 2+ active load generators/decent traffic
        if self.avg_rate >= 30:
            self.target_replicas = 3


    def ScaleOrchestrator(self, openshift):
        '''
        Confirm OpenShift oauth2 token validity and re-auth if required
        '''
        if not openshift.ValidateToken():
            openshift.Auth()    
        ''' 
        Retrieve current replicas
        '''
        self.current_replicas = openshift.RetrReplicas(self.openshift_namespace, self.openshift_deploymentconfig)
        logging.debug('{} current replicas {}'.format(self.name, self.current_replicas))
        '''
        Determine current to desired replicas
        '''
        if(self.target_replicas > self.current_replicas) or (self.target_replicas < self.current_replicas):
            logging.info('{} scaling {} from {} to {} rate average {}'.format(
                self.name, self.openshift_deploymentconfig, self.current_replicas, self.target_replicas, self.avg_rate))            
            '''
            Scale out/in based on retrieved scale rate and update
            current replicas
            '''
            openshift.SetReplicas(self.openshift_namespace, self.openshift_deploymentconfig, self.target_replicas)
            self.current_replicas = self.target_replicas
            logging.info('{} scaled {} replicas {}'.format(
                scaler.name, scaler.openshift_deploymentconfig, scaler.current_replicas))        


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
            '''
            Poll router stats
            '''
            Router.RetrStats(router)

            for scaler in scalers:
            
                '''
                Aggregate polled rate for router_backends
                '''
                Scalinator.ScaleAggregator(scaler, Router.RetrBackendRate(router, scaler.router_backend))
                logging.debug('{} rate aggregation {}'.format(scaler.name, scaler.rate_aggr)) 

                '''
                Retrieve a moving average for rate aggregations 
                '''
                Scalinator.ScaleMedian(scaler)
                logging.debug('{} average rate {}'.format(scaler.name, scaler.avg_rate))

                '''
                Retrieve target replicas based on averaged rate
                '''
                Scalinator.ScaleArbiter(scaler)
                logging.debug('{} target replicas {}'.format(scaler.name, scaler.target_replicas))

                '''
                Effect scale action based on target replicas
                '''
                Scalinator.ScaleOrchestrator(scaler, openshift)

        except KeyboardInterrupt:
            pass
        finally:
            pass
    except (KeyError, ValueError, AttributeError, TypeError) as env_error:
        logging.error(env_error)        
        raise
    except Exception as error:
        logging.error(error)
        raise
