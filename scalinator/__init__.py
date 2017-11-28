"""Scalinator : rate based pod autoscaling within Red Hat OpenShift."""
# !/usr/bin/env/python
# Author(s): Julian Gericke <julian@lsd.co.za>
# (c) LSD Information Technology
# http://www.lsd.co.za
import sys
import logging
from os import environ
from .openshift import *
from .router import *
from .scalinator import *

try:
    if 'SCALINATOR_LOGLEVEL' in environ:
        logging.basicConfig(stream=sys.stdout, level=environ.get('SCALINATOR_LOGLEVEL'),
                            format='%(asctime)s %(name)s %(levelname)s' +
                            ' %(message)s ')
    else:
        logging.basicConfig(stream=sys.stdout, level='INFO',
                            format='%(asctime)s %(name)s %(levelname)s' +
                            ' %(message)s ')
    logger = logging.getLogger(__name__)
except (KeyError, ValueError, AttributeError, Exception) as error:
    raise
