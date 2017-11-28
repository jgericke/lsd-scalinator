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
                 scalinator_openshift_namespace, scalinator_openshift_deploymentconfig):
        self.name = scalinator_name
        self.sample_length = scalinator_sample_length
        self.router_backend = scalinator_router_backend
        self.openshift_namespace = scalinator_openshift_namespace
        self.openshift_deploymentconfig = scalinator_openshift_deploymentconfig
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
        purge oldest rate aggregation
        '''
        if len(self.rate_aggr) > self.sample_length:
            del self.rate_aggr[0]
        '''
        Average rate for rate aggregation (rate_aggr)
        '''
        try:
            if len(self.rate_aggr) == self.sample_length:
                self.avg_rate = int(
                    round(sum(self.rate_aggr) / float(len(self.rate_aggr))))
        except ZeroDivisionError:
            pass

    def ScaleArbiter(self):
        '''
        Scaling on pre-calculated thresholds is kinda weak...
        - Ideally this would be a moving average based decision
        - Ideally-ier additional metrics such as req_rate, rtime and scur
          would be factored in
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
        if (self.target_replicas > self.current_replicas or
                self.target_replicas < self.current_replicas):
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
