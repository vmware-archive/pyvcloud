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
from pyvcloud.schema.vcd.v1_5.schemas.vcloud import sessionType, organizationType

class VCS(object):

    def __init__(self, url, username, org, instance, api_url, org_url, version='5.7', verify=True):
        self.url = url
        self.username = username
        self.token = None
        self.org = org
        self.instance = instance
        self.version = version
        self.verify = verify
        self.api_url = api_url
        self.org_url = org_url
        self.organization = None
        
    def get_vcloud_headers(self):
        headers = {}
        headers["x-vcloud-authorization"] = self.token
        headers["Accept"] = "application/*+xml;version=" + self.version
        return headers
        
    def login(self, password=None, token=None):
        if token:
            headers = {}
            headers["x-vcloud-authorization"] = token
            headers["Accept"] = "application/*+xml;version=" + self.version
            response = requests.get(self.org_url, headers=headers, verify=self.verify)
            if response.status_code == requests.codes.ok:
                self.token = token
                self.organization = organizationType.parseString(response.content, True)
                return True
            else:
                return False
        else:
            encode = "Basic " + base64.standard_b64encode(self.username + "@" + self.org + ":" + password)
            headers = {}
            headers["Authorization"] = encode.rstrip()
            headers["Accept"] = "application/*+xml;version=" + self.version
            response = requests.post(self.url, headers=headers, verify=self.verify)
            if response.status_code == requests.codes.ok:
                self.token = response.headers["x-vcloud-authorization"]
                session = sessionType.parseString(response.content, True)
                self.org_url = filter(lambda link: link.type_ == 'application/vnd.vmware.vcloud.org+xml', session.Link)[0].href
                return True                        
            else:
                return False
                    