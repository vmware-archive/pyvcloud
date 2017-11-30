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


class Cluster(object):

    def __init__(self, client):
        self.client = client
        self._uri = self.client.get_api_uri() + '/cluster'

    def get_clusters(self):
        method = 'GET'
        uri = self._uri
        response = self.client._do_request_prim(
            method,
            uri,
            self.client._session,
            contents=None,
            media_type=None,
            accept_type='application/*+json',
            auth=None)
        if response.status_code == requests.codes.ok:
            return json.loads(response.content.decode("utf-8"))
        else:
            raise Exception(json.loads(response.content))

    def create_cluster(self, vdc, network_name, name, node_count=2,
                       cpu_count=None, memory=None, storage_profile=None,
                       ssh_key=None):
        """
        Create a new Kubernetes cluster
        :param vdc: (str): The name of the vdc backing the org in which the cluster would be created
        :param network_name: (str): The name of the network to which the cluster vApp will connect to
        :param name: (str): The name of the cluster
        :param node_count: (str): The number of slave nodes
        :param cpu_count: (str): The number of virtual cpus on each of the nodes in the cluster
        :param memory: (str): The amount of memory (in MB) on each of the nodes in the cluster
        :param storage_profile: (str): The name of the storage profile which will back the cluster
        :param ssh_key: (str): The ssh key that clients can use to log into the node vms without explicitly providing passwords
        :return: (json) A parsed json object describing the requested cluster.
        """  # NOQA
        method = 'POST'
        uri = self._uri
        data = {'name': name, 'node_count': node_count, 'vdc': vdc,
                'cpu_count': cpu_count,
                'memory': memory,
                'network': network_name,
                'storage_profile': storage_profile,
                'ssh_key': ssh_key}
        response = self.client._do_request_prim(
            method,
            uri,
            self.client._session,
            contents=data,
            media_type=None,
            accept_type='application/*+json')
        if response.status_code == requests.codes.accepted:
            return json.loads(response.content)
        else:
            raise Exception(json.loads(response.content).get('message'))

    def delete_cluster(self, cluster_name):
        method = 'DELETE'
        uri = '%s/%s' % (self._uri, cluster_name)
        response = self.client._do_request_prim(
            method,
            uri,
            self.client._session,
            accept_type='application/*+json')
        if response.status_code == requests.codes.accepted:
            return json.loads(response.content)
        else:
            raise Exception(json.loads(response.content).get('message'))

    def get_config(self, cluster_name):
        method = 'GET'
        uri = '%s/%s/config' % (self._uri, cluster_name)
        response = self.client._do_request_prim(
            method,
            uri,
            self.client._session,
            contents=None,
            media_type=None,
            accept_type='text/x-yaml',
            auth=None)
        if response.status_code == requests.codes.ok:
            return response.content.decode('utf-8').replace('\\n', '\n')[1:-1]
        else:
            raise Exception(json.loads(response.content))
