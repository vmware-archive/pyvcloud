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


import requests
import json
from pyvcloud import _get_logger, Http


class SQLAir(object):

    def __init__(self, host=None, token=None, version='5.7',
                 verify=True, log=False):
        self.token = token
        self.version = version
        self.verify = verify
        self.org_url = None
        self.response = None
        self.host = host
        self.logger = _get_logger() if log else None

    def get_headers(self):
        headers = {}
        headers["vca-token"] = self.token
        return headers

    def ping(self):
        self.response = Http.get(self.host + '/appsrv/api/v1/services/mssql/',
                                 headers=self.get_headers(),
                                 verify=self.verify, logger=self.logger)
        return self.response.status_code

    def get_service(self, service_code='mssql'):
        self.response = Http.get(self.host + '/appsrv/api/v1/services/%s/' %
                                 service_code, headers=self.get_headers(),
                                 verify=self.verify, logger=self.logger)
        if self.response.status_code == requests.codes.ok:
            return json.loads(self.response.content)
        else:
            raise Exception(self.response.status_code)

    def get_instances(self, service_code='mssql'):
        self.response = Http.get(self.host + '/appsrv/%s/v1/instances/' %
                                 service_code, headers=self.get_headers(),
                                 verify=self.verify, logger=self.logger)
        if self.response.status_code == requests.codes.ok:
            return json.loads(self.response.content)
        else:
            raise Exception(self.response.status_code)

    def get_instance(self, instance_id, service_code='mssql'):
        self.response = Http.get(self.host + '/appsrv/%s/v1/instances/%s' %
                                 (service_code, instance_id),
                                 headers=self.get_headers(),
                                 verify=self.verify,
                                 logger=self.logger)
        if self.response.status_code == requests.codes.ok:
            return json.loads(self.response.content)
        else:
            raise Exception(self.response.status_code)
