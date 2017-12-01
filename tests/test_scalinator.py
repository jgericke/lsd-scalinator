"""Scalinator : rate based pod autoscaling within Red Hat OpenShift."""
# !/usr/bin/env/python
# Author(s): Julian Gericke <julian@lsd.co.za>
# (c) LSD Information Technology
# http://www.lsd.co.za
import os
import pytest
import scalinator


def test_scalinator_creation():
    t_router_uri = os.environ['ROUTER_URI']
    t_router_user = os.environ['ROUTER_USER']
    t_router_passwd = os.environ['ROUTER_PASSWD']
    t_router_poll_interval = os.environ['ROUTER_POLL_INTERVAL']
    t_openshift_uri = os.environ['OPENSHIFT_URI']
    t_openshift_user = os.environ['OPENSHIFT_USER']
    t_openshift_passwd = os.environ['OPENSHIFT_PASSWD']
    t_scalinator_loglevel = os.environ['SCALINATOR_LOGLEVEL']
    t_scalinator_config = os.environ['SCALINATOR_CONFIG']
