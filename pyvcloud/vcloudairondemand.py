# VMware vCloud Python SDK
# Copyright (c) 2014 VMware, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# coding: utf-8

import base64
import requests
import StringIO
import json
from pyvcloud.schema.vcim import serviceType, vchsType
from pyvcloud.schema.vchs.ondemand.sc.sc import serviceplanType
from pyvcloud.vclouddirector import VCD

class VCAOD(object):

    def __init__(self):
        self.host = None
        self.token = None
        self.type = 'ondemand'

    def login(self, iamhost, host, username, password, token=None):
        """
        Request to login to vCloud Air On Demand.
        
        :param host: URL of the vCloud service, for example: vchs.vmware.com.
        :param username: The user name.
        :param password: The password.
        :param token: The token from a previous successful login, None if this is a new login request.                        
        :return: True if the user was successfully logged in, False otherwise.
        """

        if not (iamhost.startswith('https://') or iamhost.startswith('http://')):
            iamhost = 'https://' + iamhost        
        if not (host.startswith('https://') or host.startswith('http://')):
            host = 'https://' + host            
        if token:
            headers = {}
            headers["Authorization"] = "Bearer %s" % token
            headers["Accept"] = "application/json;version=5.7;class=com.vmware.vchs.sc.restapi.model.planlisttype'"
            response = requests.get(host + "/api/sc/plans", headers=headers)
            if response.status_code == requests.codes.ok:
                self.host = host
                self.token = token
                return True
            else:
                return False
        else:
            url = iamhost + "/api/iam/login"
            encode = "Basic " + base64.encodestring(username + ":" + password)
            headers = {}
            headers["Authorization"] = encode.rstrip()
            headers["Accept"] = "application/json;version=5.7"
            response = requests.post(url, headers=headers)
            if response.status_code == requests.codes.created:
                self.host = host
                self.token = response.headers["vchs-authorization"]
                return True
            else:
                return False
    
    def logout(self):
        """
        Request to logout from  vCloud Air.
        
        :return:
        """ 
        pass       
            
    def _get_vchsHeaders(self):
        headers = {}
        headers["Authorization"] = "Bearer %s" % self.token
        headers["Accept"] = "application/xml;version=5.7"
        return headers
        
    def get_plans(self):
        response = requests.get(self.host + "/api/sc/plans", headers=self._get_vchsHeaders())
        planList = serviceplanType.parseString(response.content, True)
        return planList.plans        
        
    def get_serviceReferences(self):
        response = requests.get(self.host + "/api/vchs/services", headers=self._get_vchsHeaders())
        serviceList = serviceType.parseString(response.content, True)
        return serviceList.get_Service()
    
    def get_vdcReferences(self, serviceReference):
        response = requests.get(serviceReference.get_href(), headers=self._get_vchsHeaders())
        compute = vchsType.parseString(response.content, True)
        return compute.get_VdcRef()
        
    def get_vdcReference(self, serviceId, vdcId):
        serviceReferences = filter(lambda serviceReference: serviceReference.get_serviceId().lower() == serviceId.lower(), self.get_serviceReferences())
        if serviceReferences:
            serviceReference = serviceReferences[0]
            vdcReferences = filter(lambda vdcRef: vdcRef.get_name().lower() == vdcId.lower(), self.get_vdcReferences(serviceReference))
            if vdcReferences:
                return (True, vdcReferences[0])
            else:
                return (False, None)
        else:
            return (False, None)        
            
    def create_vCloudSession(self, vdcReference):
        response = requests.get(vdcReference.get_href(), headers=self._get_vchsHeaders())
        compute = vchsType.parseString(response.content, True)
        link = filter(lambda link: link.get_type() == "application/xml;class=vnd.vmware.vchs.vcloudsession",
                      compute.get_Link())[0]
        response = requests.post(link.get_href(), headers = self._get_vchsHeaders())
        if response.status_code == requests.codes.created:
            vCloudSession = vchsType.parseString(response.content, True)
            return vCloudSession            
        
    def get_vCloudDirector(self, serviceId, vdcId):
        vdcReference = self.get_vdcReference(serviceId, vdcId)
        if vdcReference[0] == True:
            #todo: check if vcloud session can be cached as well...
            vCloudSession = self.create_vCloudSession(vdcReference[1])
            if vCloudSession:
                vcd = VCD(vCloudSession, serviceId, vdcId)
                return vcd
        return None
        


