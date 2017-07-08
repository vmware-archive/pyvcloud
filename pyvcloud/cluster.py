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

import json
from pyvcloud import _get_logger
from pyvcloud import Http
import requests
from urlparse import urlparse


class Cluster(object):

    def __init__(self, session, verify, log=False):
        self.vcloud_session = session
        self.verify = verify
        self.response = None
        self.logger = _get_logger() if log else None
        o = urlparse(self.vcloud_session.url)
        self.api_url = '%s://%s%s' % (o.scheme, o.netloc, '/api/cluster')
        self.username = self.vcloud_session.username
        self.org_id = self.vcloud_session.organization.get_id().split(':')[-1]

    def ping(self):
        self.response = Http.get(self.api_url,
                                 headers=self.vcloud_session.
                                 get_vcloud_headers(),
                                 verify=self.verify,
                                 logger=self.logger)
        return self.response.status_code

    def get_clusters(self):
        headers = self.vcloud_session.get_vcloud_headers()
        self.response = Http.get(self.api_url, headers=headers,
                                 verify=self.verify, logger=self.logger)
        if self.response.status_code == requests.codes.ok:
            return json.loads(self.response.content)
        else:
            raise Exception(self.response.status_code)

    def create_cluster(self, vdc, network_name, name, node_count=2):
        headers = self.vcloud_session.get_vcloud_headers()
        data = {'name': name, 'node_count': node_count, 'vdc': vdc,
                'network': network_name}
        self.response = Http.post(self.api_url,
                                  headers=headers, data=json.dumps(data),
                                  verify=self.verify,
                                  logger=self.logger)
        if self.response.status_code == requests.codes.accepted:
            return json.loads(self.response.content)
        else:
            raise Exception(self.response.status_code)

    def delete_cluster(self, cluster_id):
        url = '%s/%s' % (self.api_url, cluster_id)
        self.response = Http.delete(url,
                                    headers=self.vcloud_session.
                                    get_vcloud_headers(),
                                    verify=self.verify,
                                    logger=self.logger)
        if self.response.status_code == requests.codes.accepted:
            return json.loads(self.response.content)
        else:
            raise Exception(self.response.status_code)
