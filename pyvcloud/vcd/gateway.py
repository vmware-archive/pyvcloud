# VMware vCloud Director Python SDK
# Copyright (c) 2014-2018 VMware, Inc. All Rights Reserved.
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

from pyvcloud.vcd.client import E
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import find_link
from pyvcloud.vcd.client import QueryResultFormat
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.client import ResourceType
from pyvcloud.vcd.exceptions import EntityNotFoundException
from pyvcloud.vcd.exceptions import InvalidParameterException
from pyvcloud.vcd.exceptions import MultipleRecordsException
from pyvcloud.vcd.utils import get_admin_href
from pyvcloud.vcd.vdc import VDC


class Gateway(object):
    def __init__(self, client, name=None, href=None, resource=None):
        """Constructor for Gateway objects.

        :param pyvcloud.vcd.client.Client client: the client that will be used
            to make REST calls to vCD.
        :param str name: name of the entity.
        :param str href: URI of the entity.
        :param lxml.objectify.ObjectifiedElement resource: object containing
            EntityType.EDGE_GATEWAY XML data representing the gateway.
        """
        self.client = client
        self.name = name
        if href is None and resource is None:
            raise InvalidParameterException(
                "Gateway initialization failed as arguments are either "
                "invalid or None")
        self.href = href
        self.resource = resource
        if resource is not None:
            self.name = resource.get('name')
            self.href = resource.get('href')
        self.href_admin = get_admin_href(self.href)

    def get_resource(self):
        """Fetches the XML representation of the gateway from vCD.

        Will serve cached response if possible.

        :return: object containing EntityType.EDGE_GATEWAY XML data
        representing the gateway.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.reload()
        return self.resource

    def reload(self):
        """Reloads the resource representation of the gateway.

        This method should be called in between two method invocations on the
        Gateway object, if the former call changes the representation of the
        gateway in vCD.
        """
        self.resource = self.client.get_resource(self.href)
        if self.resource is not None:
            self.name = self.resource.get('name')
            self.href = self.resource.get('href')

    def get_gateway(self, name):
        """Get a gateway.

        :param str name: name of the gateway to be fetched.

        :return: gateway

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: EntityNotFoundException: if the named gateway can not be
        found.
        :raises: MultipleRecordsException: if the multiple gateway found
        with same name.
        """
        name_filter = ('name', name)
        query = self.client.get_typed_query(
            ResourceType.EDGE_GATEWAY.value,
            query_result_format=QueryResultFormat.RECORDS,
            equality_filter=name_filter)
        records = list(query.execute())
        if records is None or len(records) == 0:
            raise EntityNotFoundException(
                'Gateway with name \'%s\' not found.' % name)
        elif len(records) > 1:
            raise MultipleRecordsException("Found multiple gateway named "
                                           "'%s'," % name)
        return records

    def get_resource_href(self, name):
        """Fetches href of a gateway from vCD.

        :param str name: name of the gateway.
        :param pyvcloud.vcd.client.EntityType entity_type: type of entity we
            want to retrieve. *Please note that this function is incapable of
            returning anything other than vApps at this point.*

        :return: href of the gateway identified by its name.

        :rtype: str
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        vdc_href = find_link(self.resource, RelationType.UP,
                             EntityType.VDC_ADMIN.value).href
        vdc = VDC(self.client, href=vdc_href)
        record = vdc.get_gateway(name)

        href = record.get('href')
        return href

    def convert_to_advanced(self, name):
        """Convert to advanced gateway.

        :param str name: name of the gateway.

        :return: object containing EntityType.EDGE_GATEWAY XML data
        representing the gateway.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: EntityNotFoundException: if the named gateway can't be found.
        """
        self.client.get_resource(self.get_resource_href(name))
        if self.resource is None:
            raise EntityNotFoundException('Gateway not found with name '
                                          '\'%s\'' % name)

        return self.client.post_linked_resource(self.resource,
                                                RelationType.
                                                CONVERT_TO_ADVANCED_GATEWAY,
                                                None, None)

    def enable_distributed_routing(self, name, enable=True):
        """Enable Distributed Routing.

        :param str name: name of the gateway.

        :return: object containing EntityType.EDGE_GATEWAY XML data
        representing the gateway.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: EntityNotFoundException: if the named gateway can't be found.
        """
        gateway = self.client.get_resource(self.get_resource_href(name))
        if gateway is None:
            raise EntityNotFoundException('Gateway not found with name '
                                          '\'%s\'' % name)
        saved_dr_status = gateway.Configuration.DistributedRoutingEnabled
        if enable == saved_dr_status:
            return
        gateway.Configuration.DistributedRoutingEnabled = \
            E.DistributedRoutingEnabled(enable)
        return self.client.put_linked_resource(self.resource,
                                               RelationType.EDIT,
                                               EntityType.EDGE_GATEWAY.value,
                                               gateway)
