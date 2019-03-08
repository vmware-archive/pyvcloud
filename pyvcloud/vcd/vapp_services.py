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
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import find_link
from pyvcloud.vcd.client import QueryResultFormat
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.client import ResourceType
from pyvcloud.vcd.exceptions import EntityNotFoundException
from pyvcloud.vcd.exceptions import InvalidParameterException
from pyvcloud.vcd.exceptions import MultipleRecordsException


class VappServices(object):
    def __init__(self,
                 client,
                 vapp_name=None,
                 network_name=None,
                 resource_href=None,
                 resource=None):
        """Constructor for VappServices objects(DHCP,NAT,Firewall etc..).

        :param pyvcloud.vcd.client.Client client: the client that will be used
            to make REST calls to vCD.
        :param str vapp_name: name of the vapp entity.
        :param str network_name: name of the vapp network entity.
        :param str resource_href: Service href.
        :param lxml.objectify.ObjectifiedElement resource: object containing
            EntityType.Service XML data representing the Service.
        :raises: InvalidParameterException: Service Initialization failed as
            arguments are either invalid or None.
        """
        self.client = client
        self.vapp_name = vapp_name
        if vapp_name is not None and network_name is not None and\
                resource_href is None and resource is None:
            self.network_name = network_name
            self._build_self_href()
        if resource_href is None and resource is None and self.href is None:
            raise InvalidParameterException(
                "Service Initialization failed as arguments are either "
                "invalid or None")
        if resource_href is not None:
            self.resource_href = resource_href
            self.href = resource_href
            self._get_resource()
            self.parent_href = find_link(self.resource, RelationType.UP,
                                         EntityType.VAPP).href
            self.parent = self.client.get_resource(self.parent_href)
        self.resource = resource

    def _build_self_href(self):
        self.parent = self._get_parent_by_name()
        self.parent_href = self.parent.get('href')
        self.href = find_link(
            self.client.get_resource(self.parent_href),
            RelationType.DOWN,
            EntityType.vApp_Network.value,
            name=self.network_name).href

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
        """Reloads the resource representation of the Vapp network."""
        self.resource = self.client.get_resource(self.href)

    def _get_parent_by_name(self):
        """Get a vapp by name.

        :return: vapp
        :rtype: lxml.objectify.ObjectifiedElement​
        :raises: EntityNotFoundException: if the named gateway can not be
            found.
        :raises: MultipleRecordsException: if more than one gateway with the
            provided name are found.
        """
        name_filter = ('name', self.vapp_name)
        query = self.client.get_typed_query(
            ResourceType.ADMIN_VAPP.value,
            query_result_format=QueryResultFormat.RECORDS,
            equality_filter=name_filter)
        records = list(query.execute())
        if records is None or len(records) == 0:
            raise EntityNotFoundException(
                'Vapp with name \'%s\' not found.' % self.vapp_name)
        elif len(records) > 1:
            raise MultipleRecordsException("Found multiple vapp named "
                                           "'%s'," % self.vapp_name)
        return records[0]
