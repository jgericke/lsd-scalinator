# ![scalinator](docs/logo.png?raw=true "scalinator") Scalinator

A pod autoscaler which uses Red Hat OpenShift's router metrics to make scale decisions.

### Build

python setup.py [develop|build]

### Usage

Define relevant environment variables (see bin/env)


### Notes

When running ose-haproxy-router image version v3.6.173 and above remove the 
ROUTER_METRICS_TYPE envar to permit external access to the haproxy stats endpoint (oc env dc router ROUTER_METRICS_TYPE-)

![](docs/arch.png)

### Author
Julian Gericke
###### LSD Information Technology
###### julian@lsd.co.za 
2017
 
