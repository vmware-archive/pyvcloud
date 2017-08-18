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
import requests
from urlparse import urlparse
import bravado
from bravado.client import SwaggerClient
from bravado.swagger_model import load_file
from bravado.requests_client import RequestsClient

TIMEOUT_SECONDS = 20

class Cluster(object):

    def __init__(self, client):
        self.client = client
        self._uri = self.client.get_api_uri()
        self.bravado_client = None
        self.__connect()

    def __connect(self):
        headers=self.__get_headers()
        response = requests.get('%s/cluster/swagger.json' % \
            (self._uri), headers=headers, verify=self.client._verify_ssl_certs)
        if response.status_code == requests.status_codes.codes.OK:
            spec = response.json()
            http_client=RequestsClient()
            http_client.session.verify = self.client._verify_ssl_certs
            config = {
                'validate_swagger_spec': True
            }
            self.bravado_client = SwaggerClient.from_spec(spec, http_client=http_client, config=config)
            self.bravado_client.swagger_spec.api_url = self._uri
        else:
            raise Exception(response)

    def __get_headers(self):
        headers={}
        headers['x-vcloud-authorization']=self.client._session.headers['x-vcloud-authorization']
        headers['Accept'] = "application/*+xml;version=" + self.client._api_version
        return headers

    def get_clusters(self):
        header={}
        header['headers'] = self.__get_headers()
        response = self.bravado_client.cluster.listClusters(_request_options=header).result(timeout=TIMEOUT_SECONDS)
        return response

    def create_cluster(self, vdc, network_name, name, node_count=2):
        header={}
        header['headers'] = self.__get_headers()
        data = {'name': name, 'node_count': node_count, 'vdc': vdc,
                'network': network_name}
        non_formatted_response = self.bravado_client.cluster.createCluster(_request_options=header, clusterConfig=data).result(timeout=TIMEOUT_SECONDS)
        response = {
            'name': non_formatted_response['name'],
            'cluster_id': non_formatted_response['cluster_id'],
            'status': non_formatted_response['status'],
            'task id': non_formatted_response['task_id']
        } 
        return response

    def delete_cluster(self, cluster_id):
        header={}
        header['headers'] = self.__get_headers()
        non_formatted_response = self.bravado_client.cluster.deleteCluster(_request_options= header, clusterid=cluster_id).result(timeout=TIMEOUT_SECONDS)
        response = {
            'name': non_formatted_response['name'],
            'cluster_id': non_formatted_response['cluster_id'],
            'status': non_formatted_response['status'],
            'task id': non_formatted_response['task_id']
        } 
        return response
