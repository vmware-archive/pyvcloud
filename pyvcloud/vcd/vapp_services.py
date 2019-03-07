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
from pyvcloud.vcd.utils import build_network_url_from_vapp_url


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
        :param: str resource_id: Service resource id
        :param str resource_href: Service href.
        :param lxml.objectify.ObjectifiedElement resource: object containing
            EntityType.Service XML data representing the Service.
        """
        self.client = client
        self.vapp_name = vapp_name
        if vapp_name is not None and network_name is not None and\
                resource_href is None and resource is None:
            self.network_name = network_name
            self._build_network_href()
            self._build_self_href()
        if resource_href is None and resource is None and \
                network_name is None and self.href is None:
            raise InvalidParameterException(
                "Service Initialization failed as arguments are either "
                "invalid or None")
        if resource_href is not None:
            self.resource_href = resource_href
            self.href = resource_href
        self.resource = resource

    def _build_self_href(self):
        pass

    def _extract_id(self, self_href):
        pass

    def _build_network_href(self):
        self.parent = self._get_parent_by_name()
        self.parent_href = self.parent.get('href')
        self.network_url = build_network_url_from_vapp_url(
            self.client.get_resource(self.parent_href), self.network_name)

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
