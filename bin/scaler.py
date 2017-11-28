"""Scalinator : rate based pod autoscaling within Red Hat OpenShift."""
# !/usr/bin/env/python
# Author(s): Julian Gericke <julian@lsd.co.za>
# (c) LSD Information Technology
# http://www.lsd.co.za
import biome
import logging
import time
from scalinator import Scalinator, OpenShift, Router
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    try:
        scalers = []
        router_scheduler = BackgroundScheduler()
        router_poll_interval = biome.ROUTER.poll_interval
        router = Router(biome.ROUTER.uri, biome.ROUTER.user,
                        biome.ROUTER.passwd)
        openshift = OpenShift(biome.OPENSHIFT.uri,
                              biome.OPENSHIFT.user, biome.OPENSHIFT.passwd)
        for cfg in range(len(biome.SCALINATOR.get_dict('config')['scalers'])):
            scalers.append(Scalinator(
                biome.SCALINATOR.get_dict('config')['scalers'][cfg]['name'],
                biome.SCALINATOR.get_dict('config')['scalers'][cfg]['sample_length'],
                biome.SCALINATOR.get_dict('config')['scalers'][cfg]['router_backend'],
                biome.SCALINATOR.get_dict('config')['scalers'][cfg]['openshift_namespace'],
                biome.SCALINATOR.get_dict('config')['scalers'][cfg]['openshift_deploymentconfig']))
        '''
        '''
        try:
            router_scheduler.add_job(Router.RetrStats, 'interval', [router], seconds=router_poll_interval, id='retrstats')
            router_scheduler.start()
            while True:
                for (index, scaler) in enumerate(scalers):
                    if hasattr(router, 'stats'):
                        '''
                        Aggregate polled rate for router_backends
                        '''
                        Scalinator.ScaleAggregator(
                            scaler, Router.RetrBackendRate(router, scaler.router_backend))
                        logging.debug('{} rate aggregation {}'.format(
                            scaler.name, scaler.rate_aggr))

                        '''
                        Retrieve a moving average for rate aggregations
                        '''
                        Scalinator.ScaleMedian(scaler)

                        if hasattr(scaler, 'avg_rate'):
                            logging.debug('{} average rate {}'.format(scaler.name, scaler.avg_rate))

                            '''
                            Retrieve target replicas based on averaged rate
                            '''
                            Scalinator.ScaleArbiter(scaler)
                            logging.debug('{} target replicas {}'.format(scaler.name, scaler.target_replicas))

                            '''
                            Retrieve current replicas
                            '''
                            ScaleRetrReplicas(scaler, openshift)
                            logging.debug('{} current replicas {}'.format(scaler.name, scaler.current_replicas))




                time.sleep(router_poll_interval)

        except (KeyboardInterrupt, SystemExit):
            router_scheduler.shutdown(wait=False)
            pass
    except (KeyError, ValueError, AttributeError, TypeError) as env_error:
        logging.error(env_error)
        raise
    except Exception as error:
        logging.error(error)
        raise
