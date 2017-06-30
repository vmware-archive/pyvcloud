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
import StringIO
import json
import logging
from pyvcloud.schema.vcd.v1_5.schemas.vcloud import sessionType, organizationType
from pyvcloud import _get_logger, Http


class VCS(object):

    def __init__(
            self,
            url,
            username,
            org,
            instance,
            api_url,
            org_url,
            version='5.7',
            verify=True,
            log=False):
        self.url = url
        self.username = username
        self.user_id = None
        self.token = None
        self.org = org
        self.instance = instance
        self.version = version
        self.verify = verify
        self.api_url = api_url
        self.org_url = org_url
        self.organization = None
        self.response = None
        self.session = None
        self.log = log
        self.logger = _get_logger() if log else None

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
            self.response = Http.get(
                self.org_url,
                headers=headers,
                verify=self.verify,
                logger=self.logger)
            if self.response.status_code == requests.codes.ok:
                self.token = token
                self.organization = organizationType.parseString(
                    self.response.content, True)
                return True
            else:
                return False
        else:
            headers = {}
            headers["Accept"] = "application/*+xml;version=" + self.version
            self.response = Http.post(
                self.url,
                headers=headers,
                auth=(
                    self.username +
                    "@" +
                    self.org,
                    password),
                verify=self.verify,
                logger=self.logger)
            if self.response.status_code == requests.codes.ok:
                self.token = self.response.headers["x-vcloud-authorization"]
                self.session = sessionType.parseString(
                    self.response.content, True)
                self.org_url = filter(
                    lambda link: link.type_ == 'application/vnd.vmware.vcloud.org+xml',
                    self.session.Link)[0].href
                return True
            else:
                return False

    def get_Link(self):
        if self.organization:
            return self.organization.Link
        elif self.session:
            return self.session.Link
        else:
            return False

    def update_session_data(self, token):
        headers = {}
        headers["x-vcloud-authorization"] = token
        headers["Accept"] = "application/*+xml;version=" + self.version
        self.response = Http.get(self.url, headers=headers, verify=self.verify, logger=self.logger)
        if self.response.status_code == requests.codes.ok:
            self.session = sessionType.parseString(self.response.content, True)
            self.org_url = filter(lambda link: link.type_ == 'application/vnd.vmware.vcloud.org+xml', self.session.Link)[0].href
            self.username = self.session.get_user()
            self.user_id = self.session.get_userId().split(':')[-1]
            self.org = self.session.get_org()
            self.org_id = self.org_url.split('/')[-1]
            self.response = Http.get(self.org_url, headers=headers, verify=self.verify, logger=self.logger)
            if self.response.status_code == requests.codes.ok:
                self.token = token
                self.organization = organizationType.parseString(self.response.content, True)
                return True
            else:
                return False
        else:
            return False
