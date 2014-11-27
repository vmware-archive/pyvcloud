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

import requests
from gateway import Gateway
from schema.vcd.v1_5.schemas.vcloud import vdcType, queryRecordViewType, networkType
# from helper import generalHelperFunctions as ghf

class VCD(object):

    def __init__(self, vCloudSession, serviceId, vdcId):
        vdcLink = vCloudSession.get_VdcLink()
        self.token = vdcLink.get_authorizationToken()
        self.defaultVersion = "5.6"
        self.headers = self._get_vcdHeaders()
        self.href = vdcLink.get_href()
        self.service = serviceId
        self.vdc = vdcId        

    def _get_vcdHeaders(self):
        headers = {}
        headers["x-vcloud-authorization"] = self.token
        headers["Accept"] = "application/*+xml;version=" + self.defaultVersion
        return headers

    def _get_vdc(self):
        response = requests.get(self.href, headers = self.headers)
        return vdcType.parseString(response.content, True)
        
    def get_vdcResources(self):
        vdc = self._get_vdc()
        computeCapacity = vdc.get_ComputeCapacity()
        cpu = computeCapacity.get_Cpu()
        memory = computeCapacity.get_Memory()
        storageCapacity = vdc.get_StorageCapacity()
        return (cpu, memory, storageCapacity)
        
    def get_gateways(self):
        gateways = []
        link = filter(lambda link: link.get_rel() == "edgeGateways", self._get_vdc().get_Link())
        response = requests.get(link[0].get_href(), headers = self.headers)
        queryResultRecords = queryRecordViewType.parseString(response.content, True)
        if queryResultRecords.get_Record():
            for edgeGatewayRecord in queryResultRecords.get_Record():
                response = requests.get(edgeGatewayRecord.get_href(), headers = self.headers)
                edgeGateway = networkType.parseString(response.content, True)
                gateways.append(Gateway(edgeGateway, self.headers))
        return gateways
        
    def get_gateway(self, gatewayId):
        gateways = filter(lambda gateway: gateway.get_name() == gatewayId, self.get_gateways())
        if gateways:
            return gateways[0]
        return None
               
        
        
    
        
