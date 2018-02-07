# VMware vCloud Director Python SDK
# Copyright (c) 2018 VMware, Inc. All Rights Reserved.
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

from pyvcloud.vcd.client import E_VMEXT
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import QueryResultFormat
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.utils import to_dict


class APIExtension(object):

    TYPE_NAME = 'adminService'
    ATTRIBUTES = [
        'name', 'namespace', 'enabled', 'exchange', 'routingKey', 'priority',
        'isAuthorizationEnabled', 'href', 'id'
    ]

    def __init__(self, client):
        self.client = client

    def list_extensions(self):
        """Return the API extensions defined in the system.

        :return: (dict): list with the API
            extensions defined in the system.
        """
        query = self.client.get_typed_query(
            self.TYPE_NAME, query_result_format=QueryResultFormat.ID_RECORDS)
        return [to_dict(r, self.ATTRIBUTES) for r in query.execute()]

    def get_extension(self, name, namespace=None):
        """Return the info about an API extension.

        :param name: (str): The name of the extension service.
        :param namespace: (str): The namespace of the extension service. If
            None, it will use the value defined by the `name` parameter.
        :return: (dict): dictionary with the information about the extension.
        """
        ext = self.client.get_typed_query(
            self.TYPE_NAME,
            qfilter='name==%s;namespace==%s' % (name, namespace
                                                if namespace else name),
            query_result_format=QueryResultFormat.ID_RECORDS).find_unique()
        return to_dict(ext, self.ATTRIBUTES)

    def get_api_filters(self, service_id):
        """Return the API filters defined for the service.

        :param service_id: (str): The id of the extension service.
        :return: (lxml.objectify.ObjectifiedElement): list with the API filters
            registered for the API extension.
        """
        return self.client.get_typed_query(
            'apiFilter',
            equality_filter=('service', service_id),
            query_result_format=QueryResultFormat.ID_RECORDS).execute()

    def get_extension_info(self, name, namespace=None):
        """Return the info about an API extension, including filters.

        :param name: (str): The name of the extension service.
        :param namespace: (str): The namespace of the extension service. If
            None, it will use the value defined by the `name` parameter.
        :return: (dict): dictionary with the information about the extension.
        """
        ext = self.get_extension(name, namespace)
        filters = self.get_api_filters(ext['id'])
        n = 1
        for f in filters:
            ext['filter_%s' % n] = f.get('urlPattern')
            n += 1
        return ext

    def add_extension(self, name, namespace, routing_key, exchange, patterns):
        """Add an API extension.

        :param name: (str): The name of the new API extension service.
        :param namespace: (str): The namespace of the new API extension
            service.
        :param routing_key: (str): AMQP routing key to use with the extension.
        :param exchange: (str): AMQP exchange to use with the extension.
        :param patterns: (str): URI API filters to register with the extension.
        :return: (lxml.objectify.ObjectifiedElement): object containing
            the sparse representation of the API extension.
        """
        params = E_VMEXT.Service({'name': name})
        params.append(E_VMEXT.Namespace(namespace))
        params.append(E_VMEXT.Enabled('true'))
        params.append(E_VMEXT.RoutingKey(routing_key))
        params.append(E_VMEXT.Exchange(exchange))
        filters = E_VMEXT.ApiFilters()
        for pattern in patterns:
            filters.append(
                E_VMEXT.ApiFilter(E_VMEXT.UrlPattern(pattern.strip())))
        params.append(filters)
        ext = self.client.get_extension()
        ext_services = self.client.get_linked_resource(
            ext, RelationType.DOWN, EntityType.EXTENSION_SERVICES.value)
        return self.client.post_linked_resource(ext_services, RelationType.ADD,
                                                EntityType.ADMIN_SERVICE.value,
                                                params)

    def enable_extension(self, name, enabled=True, namespace=None):
        """Enable or disable the API extension service.

        :param name: (str): The name of the extension service.
        :param namespace: (str): The namespace of the extension service. If
            None, it will use the value defined by the `name` parameter.
        :param enabled: (bool): Flag to enable or disable the extension.
        :return: (lxml.objectify.ObjectifiedElement): object containing
            the representation of the API extension.
        """
        record = self.client.get_typed_query(
            self.TYPE_NAME,
            qfilter='name==%s;namespace==%s' % (name, namespace
                                                if namespace else name),
            query_result_format=QueryResultFormat.RECORDS).find_unique()
        params = E_VMEXT.Service({'name': name})
        params.append(E_VMEXT.Namespace(record.get('namespace')))
        params.append(E_VMEXT.Enabled('true' if enabled else 'false'))
        params.append(E_VMEXT.RoutingKey(record.get('routingKey')))
        params.append(E_VMEXT.Exchange(record.get('exchange')))
        self.client.put_resource(record.get('href'), params, None)
        return record.get('href')

    def delete_extension(self, name, namespace):
        """Delete the API extension service.

        :param name: (str): The name of the extension service.
        :param namespace: (str): The namespace of the extension service. If
            None, it will use the value defined by the `name` parameter.
        :return: (lxml.objectify.ObjectifiedElement): object containing
            the representation of the API extension.
        """
        href = self.enable_extension(name, enabled=False, namespace=namespace)
        return self.client.delete_resource(href)
