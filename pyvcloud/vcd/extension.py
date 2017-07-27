# VMware vCloud Director Python SDK
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

from lxml import objectify
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import QueryResultFormat
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.utils import to_dict


Ext = objectify.ElementMaker(
    annotate=False,
    namespace='http://www.vmware.com/vcloud/extension/v1.5',
    nsmap={None: "http://www.vmware.com/vcloud/v1.5",
           'vmext': 'http://www.vmware.com/vcloud/extension/v1.5'})


class Extension(object):

    TYPE_NAME = 'adminService'
    ATTRIBUTES = ['name', 'namespace', 'enabled',
                  'exchange', 'routingKey', 'priority',
                  'isAuthorizationEnabled', 'href', 'id']

    def __init__(self, client):
        self.client = client

    def list_extensions(self):
        query = self.client.get_typed_query(
            self.TYPE_NAME,
            query_result_format=QueryResultFormat.ID_RECORDS)
        return [to_dict(r, self.ATTRIBUTES) for r in query.execute()]

    def get_extension(self, name):
        ext = self.client.get_typed_query(
            self.TYPE_NAME,
            equality_filter=('name', name),
            query_result_format=QueryResultFormat.ID_RECORDS).find_unique()
        return to_dict(ext, self.ATTRIBUTES)

    def add_extension(self, name, namespace, routing_key, exchange, patterns):
        params = Ext.Service({'name': name})
        params.append(Ext.Namespace(namespace))
        params.append(Ext.Enabled('true'))
        params.append(Ext.RoutingKey(routing_key))
        params.append(Ext.Exchange(exchange))
        filters = Ext.ApiFilters()
        for pattern in patterns:
            filters.append(Ext.ApiFilter(Ext.UrlPattern(pattern.strip())))
        params.append(filters)
        ext = self.client.get_extension()
        ext_services = self.client.get_linked_resource(
            ext,
            RelationType.DOWN,
            EntityType.EXTENSION_SERVICES.value)
        return self.client.post_linked_resource(
            ext_services,
            RelationType.ADD,
            EntityType.ADMIN_SERVICE.value,
            params)

    def enable_extension(self, name, enabled=True):
        ext = self.client.get_typed_query(
            self.TYPE_NAME,
            equality_filter=('name', name),
            query_result_format=QueryResultFormat.RECORDS).find_unique()
        params = Ext.Service({'name': name})
        params.append(Ext.Namespace(ext.get('namespace')))
        params.append(Ext.Enabled('true' if enabled else 'false'))
        params.append(Ext.RoutingKey(ext.get('routingKey')))
        params.append(Ext.Exchange(ext.get('exchange')))
        self.client.put_resource(ext.get('href'), params, None)
        return ext.get('href')

    def delete_extension(self, name):
        href = self.enable_extension(name, enabled=False)
        return self.client.delete_resource(href)
