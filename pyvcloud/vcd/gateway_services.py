# VMware vCloud Director Python SDK
# Copyright (c) 2014-2019 VMware, Inc. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from pyvcloud.vcd.client import QueryResultFormat
from pyvcloud.vcd.client import ResourceType
from pyvcloud.vcd.exceptions import EntityNotFoundException
from pyvcloud.vcd.exceptions import InvalidParameterException
from pyvcloud.vcd.exceptions import MultipleRecordsException
from pyvcloud.vcd.utils import build_network_url_from_gateway_url


class GatewayServices(object):
    # NOQA
    def __init__(self, client, gateway_name=None, resource_id=None,
                 resource_href=None, resource=None):
        """Constructor for Service objects(DHCP,NAT,Firewall etc..).

         :param pyvcloud.vcd.client.Client client: the client that will be used
            to make REST calls to vCD.
        :param str gateway_name: name of the gateway entity.
        :param: str resource_id: Service resource id
        :param str resource_href: Service href.
        :param lxml.objectify.ObjectifiedElement resource: object containing
            EntityType.Service XML data representing the Service.
        """
        self.client = client
        self.gateway_name = gateway_name

        if gateway_name is not None and \
                resource_id is not None and \
                resource_href is None and \
                resource is None:
            self._build_network_href()
            self.resource_id = resource_id
            self._build_self_href(resource_id)
        if resource_href is None and \
                resource is None and resource_id is None and self.href is None:
            raise InvalidParameterException(
                "Service Initialization failed as arguments are either "
                "invalid or None")
        if resource_href is not None:
            self.resource_href = resource_href
            self.resource_id = self._extract_id(resource_href)
            self.href = resource_href
        self.resource = resource

    def _build_self_href(self):
        pass

    def _extract_id(self, self_href):
        pass

    def _build_network_href(self):
        self.parent = self._get_parent_by_name()
        self.parent_href = self.parent.get('href')
        self.network_url = build_network_url_from_gateway_url(self.parent_href)

    def _get_resource(self):
        """Fetches the XML representation of the Service.

         :return: object containing EntityType.Service XML data
        representing the Service.
        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self._reload()
        return self.resource

    def _reload(self):
        pass

    def _get_parent_by_name(self):
        """Get a gateway by name.

        :return: gateway​
        :rtype: lxml.objectify.ObjectifiedElement​
        :raises: EntityNotFoundException: if the named gateway can not be
            found.
        :raises: MultipleRecordsException: if more than one gateway with the
            provided name are found.
        """
        name_filter = ('name', self.gateway_name)
        query = self.client.get_typed_query(
            ResourceType.EDGE_GATEWAY.value,
            query_result_format=QueryResultFormat.RECORDS,
            equality_filter=name_filter)
        records = list(query.execute())
        if records is None or len(records) == 0:
            raise EntityNotFoundException(
                'Gateway with name \'%s\' not found.' % self.gateway_name)
        elif len(records) > 1:
            raise MultipleRecordsException("Found multiple gateway named "
                                           "'%s'," % self.gateway_name)
        return records[0]
