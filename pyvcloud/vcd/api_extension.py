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
from pyvcloud.vcd.client import ResourceType
from pyvcloud.vcd.exceptions import MissingRecordException
from pyvcloud.vcd.exceptions import MultipleRecordsException
from pyvcloud.vcd.utils import to_dict


class APIExtension(object):
    ATTRIBUTES = [
        'name', 'namespace', 'enabled', 'exchange', 'routingKey', 'priority',
        'isAuthorizationEnabled', 'href', 'id'
    ]

    def __init__(self, client):
        """Constructor for APIExtension object.

        :param pyvcloud.vcd.client.Client client: the client that will be used
            to make REST calls to vCD.
        """
        self.client = client

    def list_extensions(self):
        """Fetch the API extension services defined in the system.

        :return: all the registered API extension services in the system.

        :rtype: list
        """
        query = self.client.get_typed_query(
            ResourceType.ADMIN_SERVICE.value,
            query_result_format=QueryResultFormat.ID_RECORDS)
        return [to_dict(r, self.ATTRIBUTES) for r in query.execute()]

    def _get_extension_record(self,
                              name,
                              namespace=None,
                              format=QueryResultFormat.ID_RECORDS):
        """Fetch info about a particular API extension service as a record.

        :param str name: the name of the extension service whose info we want
            to retrieve.
        :param str namespace: the namespace of the extension service. If
            omitted, all extension services matching the given name will be
            retrieved and that would lead to a MultipleRecordsException.
        :param format QueryResultFormat: dictates whether id or href should be
            part of the returned record. By default id is returned.

        :return: the extension service record.

        :rtype: generator object that returns lxml.objectify.ObjectifiedElement
            object containing AdminServiceRecord XML data representing the
            service.

        :raises MissingRecordException: if a service with the given name and
            namespace couldn't be found.
        :raise MultipleRecordsException: if more than one service with the
            given name and namespace are found.
        """
        qfilter = 'name==%s' % name
        if namespace is not None:
            qfilter += ';namespace==%s' % namespace
        try:
            ext = self.client.get_typed_query(
                ResourceType.ADMIN_SERVICE.value,
                qfilter=qfilter,
                query_result_format=format).find_unique()
        except MissingRecordException as e:
            msg = 'API Extension service (name:' + name
            if namespace is not None:
                msg += ', namespace:' + namespace
            msg += ') not found.'
            raise MissingRecordException(msg)
        except MultipleRecordsException as e:
            msg = 'Found multiple API Extension service with (name:' + name
            if namespace is not None:
                msg += ', namespace:' + namespace + ').'
            else:
                msg += '). Consider providing value for the namespace.'
            raise MultipleRecordsException(msg)

        return ext

    def get_extension(self, name, namespace=None):
        """Fetch info about a particular API extension service.

        :param str name: the name of the extension service whose info we want
            to retrieve.
        :param str namespace: the namespace of the extension service.

        :return: information about the extension service.

        :rtype: dict

        :raises MissingRecordException: if a service with the given name and
            namespace couldn't be found.
        :raise MultipleRecordsException: if more than one service with the
            given name and namespace are found.
        """
        ext_record = self._get_extension_record(name, namespace)
        return to_dict(ext_record, self.ATTRIBUTES)

    def get_api_filters(self, service_id):
        """Fetch the API filters defined for the service.

        :param str service_id: the id of the extension service.

        :return: API filters registered for the API extension.

        :rtype: generator object
        """
        return self.client.get_typed_query(
            ResourceType.API_FILTER.value,
            equality_filter=('service', service_id),
            query_result_format=QueryResultFormat.ID_RECORDS).execute()

    def get_extension_info(self, name, namespace=None):
        """Return info about an API extension, including filters.

        :param str name: the name of the extension service whose info we want
            to retrieve.
        :param str namespace: the namespace of the extension service. If not
            specified (i.e. = None), we will use the value passed in the
            `name` parameter.

        :return: information about the extension.

        :rtype: dict

        :raises MissingRecordException: if a service with the given name and
            namespace couldn't be found.
        :raise MultipleRecordsException: if more than one service with the
            given name and namespace are found.
        """
        ext = self.get_extension(name, namespace)
        filters = self.get_api_filters(ext['id'])
        n = 1
        for f in filters:
            ext['filter_%s' % n] = f.get('urlPattern')
            n += 1
        return ext

    def add_extension(self, name, namespace, routing_key, exchange, patterns):
        """Add an API extension service.

        :param str name: name of the new API extension service.
        :param str namespace: namespace of the new API extension service.
        :param str routing_key: AMQP routing key to use with the extension.
        :param str exchange: AMQP exchange to use with the extension.
        :param str patterns: URI API filters to register with the extension.

        :return: object containing EntityType.ADMIN_SERVICE XML data i.e. the
            sparse representation of the API extension.

        :rtype: lxml.objectify.ObjectifiedElement
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
        """Enable or disable an API extension service.

        :param str name: the name of the extension service whose we want to
            enable/disable.
        :param str namespace: the namespace of the extension service. If not
            specified (i.e. = None), we will use the value passed in the
            `name` parameter.
        :param bool enabled: flag to enable or disable the extension.

        :return: href of the service being enabled/disabled.

        :rtype: str

        :raises MissingRecordException: if a service with the given name and
            namespace couldn't be found.
        :raise MultipleRecordsException: if more than one service with the
            given name and namespace are found.
        """
        record = self._get_extension_record(name=name,
                                            namespace=namespace,
                                            format=QueryResultFormat.RECORDS)

        params = E_VMEXT.Service({'name': name})
        params.append(E_VMEXT.Namespace(record.get('namespace')))
        params.append(E_VMEXT.Enabled('true' if enabled else 'false'))
        params.append(E_VMEXT.RoutingKey(record.get('routingKey')))
        params.append(E_VMEXT.Exchange(record.get('exchange')))

        self.client.put_resource(record.get('href'), params, None)
        return record.get('href')

    def delete_extension(self, name, namespace):
        """Delete an API extension service.

        :param str name: the name of the extension service whose we want to
            delete.
        :param str namespace: the namespace of the extension service. If not
            specified (i.e. = None), we will use the value passed in the
            `name` parameter.

        :raises MissingRecordException: if a service with the given name and
            namespace couldn't be found.
        :raise MultipleRecordsException: if more than one service with the
            given name and namespace are found.
        """
        href = self.enable_extension(name, enabled=False, namespace=namespace)
        return self.client.delete_resource(href)
