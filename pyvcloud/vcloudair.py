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
from pyvcloud.schema.vcd.v1_5.schemas.vcloud import sessionType, organizationType
from pyvcloud.vclouddirector import VCD

class VCA(object):

    def __init__(self):
        self.host = None
        self.token = None
        self.service_type = 'subscription'
        self.version = '5.6'
        self.session = None
        self.org_name = None

    def login(self, host, username, password, token=None, service_type='subscription', version='5.6'):
        """
        Request to login to vCloud Air
        
        :param host: URL of the vCloud service, for example: vchs.vmware.com.
        :param username: The user name.
        :param password: The password.
        :param token: The token from a previous successful login, None if this is a new login request.                        
        :return: True if the user was successfully logged in, False otherwise.
        """
        
        if not (host.startswith('https://') or host.startswith('http://')):
            host = 'https://' + host
        
        if service_type == 'subscription':
            if token:
                headers = {}
                headers["x-vchs-authorization"] = token
                headers["Accept"] = "application/xml;version=" + version
                response = requests.get(host + "/api/vchs/services", headers=headers)
                if response.status_code == requests.codes.ok:
                    self.host = host
                    self.token = token
                    self.service_type = service_type
                    self.version = version
                    return True
                else:
                    return False
            else:
                url = host + "/api/vchs/sessions"
                encode = "Basic " + base64.encodestring(username + ":" + password)
                headers = {}
                headers["Authorization"] = encode.rstrip()
                headers["Accept"] = "application/xml;version=" + version
                response = requests.post(url, headers=headers)
                if response.status_code == requests.codes.created:
                    self.host = host
                    self.token = response.headers["x-vchs-authorization"]
                    self.service_type = service_type
                    self.version = version                
                    return True
                else:
                    return False
        elif service_type == 'ondemand':
            pass
        elif service_type == 'vcd':
            if token:
                url = host + "/api/session"     
                headers = {}
                headers["x-vcloud-authorization"] = token
                headers["Accept"] = "application/*+xml;version=" + version
                response = requests.get(url, headers=headers)
                if response.status_code == requests.codes.ok:
                    self.host = host
                    self.token = token
                    self.session = sessionType.parseString(response.content, True)
                    self.service_type = service_type
                    self.version = version    
                    self.org_name = username[username.rfind('@')+1:]                    
                    return True
                else:
                    return False
            else:
                url = host + "/api/sessions"                     
                encode = "Basic " + base64.encodestring(username + ":" + password)
                headers = {}
                headers["Authorization"] = encode.rstrip()
                headers["Accept"] = "application/*+xml;version=" + version
                response = requests.post(url, headers=headers)
                if response.status_code == requests.codes.ok:
                    self.host = host
                    self.token = response.headers["x-vcloud-authorization"]
                    self.service_type = service_type
                    self.version = version    
                    self.session = sessionType.parseString(response.content, True)
                    self.org_name = username[username.rfind('@')+1:]
                    return True
                else:
                    return False
        else:
            pass
    
    def logout(self):
        """
        Request to logout from  vCloud Air.
        
        :return:
        """        
        if self.service_type == 'subscription':
            url = self.host + "/api/vchs/session"
            headers = {}
            headers["x-vchs-authorization"] = self.token
            return requests.delete(url, headers=self._get_vchsHeaders())
        elif self.service_type == 'ondemand':
            pass
        elif self.service_type == 'vcd':
            self.session = None
        
    def _get_vchsHeaders(self):
        headers = {}        
        if self.service_type == 'subscription':
            headers["x-vchs-authorization"] = self.token
            headers["Accept"] = "application/xml;version=" + self.version
        elif self.service_type == 'ondemand':
            pass
        elif self.service_type == 'vcd':
            headers["x-vcloud-authorization"] = self.token
            headers["Accept"] = "application/*+xml;version=" + self.version            
        return headers
        
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
        
    def get_vCloudDirector(self, serviceId=None, vdcId=None):
        if self.service_type == 'subscription':
            vdcReference = self.get_vdcReference(serviceId, vdcId)
            if vdcReference[0] == True:
                #todo: check if vcloud session can be cached as well...
                vCloudSession = self.create_vCloudSession(vdcReference[1])
                if vCloudSession:
                    vdcLink = vCloudSession.get_VdcLink()
                    vcd = VCD(vdcLink.get_authorizationToken(), vdcLink.get_href(), self.version, serviceId, vdcId)
                    return vcd
        elif self.service_type == 'ondemand':
            pass
        elif self.service_type == 'vcd':
            if self.session:
                org_refs = filter(lambda org_ref: (org_ref.name == self.org_name and org_ref.type_ == 'application/vnd.vmware.vcloud.org+xml'), self.session.Link)
                if org_refs:
                    href = org_refs[0].href
                    response = requests.get(href, headers=self._get_vchsHeaders())
                    if response.status_code == requests.codes.ok:
                        org = organizationType.parseString(response.content, True)
                        vdc_links = filter(lambda vdc_link: (vdc_link.name == self.org_name and vdc_link.type_ == 'application/vnd.vmware.vcloud.vdc+xml'), org.Link)
                        if vdc_links:
                            vcd = VCD(self.token, vdc_links[0].href, self.version, None, self.org_name)
                            return vcd
        return None

