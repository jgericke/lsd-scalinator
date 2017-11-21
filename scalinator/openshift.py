#!/usr/bin/env python
"""
openshift : Common OpenShifty things
Author(s): Julian Gericke (julian@lsd.co.za)
(c) LSD Information Technology
http://www.lsd.co.za
"""
import requests
import urllib
import json
import logging

logger = logging.getLogger(__name__)

class OpenShift(object):

    def __init__(self, openshift_uri, openshift_user, openshift_passwd):
        self.uri = openshift_uri
        self.user = openshift_user
        self.passwd = openshift_passwd
        self.token = ''

    def Auth(self):
        '''
        Generate oauth2 token
        '''
        try:
            ocp_auth_resp = requests.get(self.uri + '/oauth/authorize?response_type=token&client_id=openshift-challenging-client',
                                         auth=(self.user, self.passwd),
                                         headers={'X-CSRF-Token': '1'},
                                         verify=False)
            ocp_auth_url = dict(urllib.parse.parse_qs(ocp_auth_resp.url))
            self.token = ocp_auth_url[u''+self.uri + '/oauth/token/implicit#access_token'][0]
        except Exception as error:
            logger.error(error)
            raise


    def ValidateToken(self):
        '''
        Validate oauth2 token
        '''
        try:
            ocp_validtoken_resp = requests.get(self.uri + '/oapi/v1/oauthaccesstokens/' + self.token,
                                               headers={
                                                   'Authorization': 'Bearer ' + self.token},
                                               verify=False)
            if 'userName' in ocp_validtoken_resp.content.decode('latin1'):
                return(True)
        except Exception as error:
            logger.error(error)
            raise




    def RetrReplicas(self, openshift_namespace, openshift_deploymentconfig):
        '''
        Return current replicas when passed a namespace and deploymentconfig
        '''    
        try:
            ocp_replicas_resp = requests.get(self.uri + '/oapi/v1/namespaces/' + openshift_namespace + '/deploymentconfigs/' + openshift_deploymentconfig + '/scale',
                                             headers={
                                                 'Authorization': 'Bearer ' + self.token},
                                             verify=False)
            return(ocp_replicas_resp.json()['status']['replicas'])
        except Exception as error:
            logger.error(error)
            raise



    def SetReplicas(self, openshift_namespace, openshift_deploymentconfig, openshift_replicas):
        '''
        Set replica count to openshift_replicas when passed a namespace and deploymentconfig
        '''
        try:
            ocp_scale_payload = {'kind': 'Scale',
                                 'apiVersion': 'extensions/v1beta1',
                                 'metadata': {
                                     'name': openshift_deploymentconfig,
                                     'namespace': openshift_namespace
                                 },
                                 'spec': {
                                     'replicas': openshift_replicas
                                 },
                                 'status': {
                                     'targetSelector': 'app=openshift_deploymentconfig,deploymentconfig=openshift_deploymentconfig'
                                 },
                                 }
            ocp_scale_dc_resp = requests.put(self.uri + '/oapi/v1/namespaces/' + openshift_namespace + '/deploymentconfigs/' + openshift_deploymentconfig + '/scale',
                                             data=json.dumps(ocp_scale_payload),
                                             headers={
                                                 'Content-type': 'application/json', 'Authorization': 'Bearer ' + self.token},
                                             verify=False)
            return(ocp_scale_dc_resp.json()['spec']['replicas'])
        except Exception as error:
            logger.error(error)
            raise
