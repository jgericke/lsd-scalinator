"""Scalinator : rate based pod autoscaling within Red Hat OpenShift."""
# !/usr/bin/env/python
# Author(s): Julian Gericke <julian@lsd.co.za>
# (c) LSD Information Technology
# http://www.lsd.co.za
import logging

logger = logging.getLogger(__name__)


class Scalinator(object):
    """Scalinator."""

    def __init__(self, scalinator_name, scalinator_sample_length, scalinator_router_backend,
                 scalinator_openshift_namespace, scalinator_openshift_deploymentconfig, scalinator_thresholds):
        self.name = scalinator_name
        self.sample_length = scalinator_sample_length
        self.router_backend = scalinator_router_backend
        self.openshift_namespace = scalinator_openshift_namespace
        self.openshift_deploymentconfig = scalinator_openshift_deploymentconfig
        self.thresholds = scalinator_thresholds
        self.rate_aggr = []

    def ScaleAggregator(self, be_rate):
        '''
        Test we have a valid BE rate to work with
        '''
        if isinstance(be_rate, int):
            '''
            Append to scaler's rate aggregation
            '''
            self.rate_aggr.append(be_rate)
            logging.debug('{} retrieved be_rate {}'.format(self.name, be_rate))
        else:
            logging.warn('{} retrieved an invalid be_rate'.format(
                self.name))

    def ScaleMedian(self):
        '''
        If aggregated rates are in excess of the defined sample length
        purge oldest rate aggregation. Cater to element 0 by decrementing
        sample_length
        '''
        if len(self.rate_aggr) > (self.sample_length - 1):
            del self.rate_aggr[0]
        '''
        Average rate for rate aggregation (rate_aggr) should occur when
        sample length is reached, again decr for element 0
        '''
        try:
            if len(self.rate_aggr) == (self.sample_length - 1):
                self.avg_rate = int(
                    round(sum(self.rate_aggr) / float(len(self.rate_aggr))))
        except ZeroDivisionError:
            pass

    def ScaleArbiter(self):
        '''
        Determine target_replicas based on avg_rate
        '''
        if self.avg_rate < self.thresholds['low']['rate_min']:
            self.target_replicas = self.thresholds['floor']['replicas']
            
            logging.info('\n{} floor replicas\n'.format(self.thresholds['floor']['replicas']))

        elif (self.avg_rate >= self.thresholds['low']['rate_min']) and (self.avg_rate <= self.thresholds['low']['rate_max']):
            self.target_replicas = self.thresholds['low']['replicas']

            logging.info('\n{} low replicas\n'.format(self.thresholds['low']['replicas']))


        elif (self.avg_rate >= self.thresholds['med']['rate_min']) and (self.avg_rate <= self.thresholds['med']['rate_max']):
            self.target_replicas = self.thresholds['med']['replicas']

            logging.info('\n{} med replicas\n'.format(self.thresholds['med']['replicas']))


        elif (self.avg_rate >= self.thresholds['high']['rate_min']) and (self.avg_rate <= self.thresholds['high']['rate_max']):
            self.target_replicas = self.thresholds['high']['replicas']

            logging.info('\n{} high replicas\n'.format(self.thresholds['high']['replicas']))

        elif self.avg_rate >= self.thresholds['ceiling']['rate_min']:
            self.target_replicas = self.thresholds['ceiling']['replicas']


            logging.info('\n{} ceiling replicas\n'.format(self.thresholds['ceiling']['replicas']))

        else:
            self.target_replicas = self.thresholds['default']['replicas']

            logging.info('\n{} default replicas\n'.format(self.thresholds['default']['replicas']))

    def ScaleRetrReplicas(self, openshift):
        '''
        Retrieve current replicas
        '''
        if not hasattr(self, 'current_replicas'):
            '''
            Confirm token validity and re-auth if required
            '''
            if not openshift.ValidateToken():
                openshift.Auth()
            self.current_replicas = openshift.RetrReplicas(
                self.openshift_namespace, self.openshift_deploymentconfig)
            logging.debug('{} current replicas {}'.format(
                self.name, self.current_replicas))

    def ScaleOrchestrator(self, openshift):
        '''
        Determine current to desired replicas
        '''
        if self.current_replicas != self.target_replicas:
            logging.info('{} scaling {} from {} to {} rate average {}'
                         .format(self.name, self.openshift_deploymentconfig,
                                 self.current_replicas, self.target_replicas,
                                 self.avg_rate))
            '''
            Confirm token validity and re-auth if required
            '''
            if not openshift.ValidateToken():
                openshift.Auth()
            '''
            Scale out/in based on retrieved scale rate and update
            current replicas
            '''
            openshift.SetReplicas(
                self.openshift_namespace, self.openshift_deploymentconfig,
                self.target_replicas)
            self.current_replicas = self.target_replicas
            logging.info('{} scaled {} replicas {}'.format(
                self.name, self.openshift_deploymentconfig,
                self.current_replicas))
