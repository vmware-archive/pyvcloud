# VMware vCloud Director Python SDK
# Copyright (c) 2014-2019 VMware, Inc. All Rights Reserved.
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
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.exceptions import InvalidParameterException
from pyvcloud.vcd.utils import get_admin_href


class VdcNetwork(object):
    def __init__(self, client, name=None, href=None, resource=None):
        """Constructor for VdcNetwork object.

        :param pyvcloud.vcd.client.Client client: the client that will be used
            to make REST calls to vCD.
        :param str name: name of the entity.
        :param str href: URI of the entity.
        :param lxml.objectify.ObjectifiedElement resource: object containing
          EntityType.ORG_VDC_NETWORK XML data representing the org vdc network.
        """
        self.client = client
        self.name = name
        if href is None and resource is None:
            raise InvalidParameterException(
                "Vdc Network initialization failed as arguments are either "
                "invalid or None")
        self.href = href
        self.resource = resource
        if resource is not None:
            self.name = resource.get('name')
            self.href = resource.get('href')
        self.href_admin = get_admin_href(self.href)

    def get_resource(self):
        """Fetches the XML representation of the org vdc network from vCD.

        Will serve cached response if possible.

        :return: object containing EntityType.ORG_VDC_NETWORK XML data
        representing the org vdc.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.reload()
        return self.resource

    def reload(self):
        """Reloads the resource representation of the org vdc network.

        This method should be called in between two method invocations on the
        Org Vdc Network object, if the former call changes the representation
        of the org vdc network in vCD.
        """
        self.resource = self.client.get_resource(self.href)
        if self.resource is not None:
            self.name = self.resource.get('name')
            self.href = self.resource.get('href')

    def edit_name_description_and_shared_state(self,
                                               name,
                                               description=None,
                                               is_shared=None):
        """Edit name, description and shared state of the org vdc network.

        :param str name: New name of org vdc network. It is mandatory.
        :param str description: New description of org vdc network
        :param bool is_shared: True if user want to share else False.

        :return: object containing EntityType.TASK XML data
            representing the asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if name is None:
            raise InvalidParameterException("Name can't be None or empty")
        vdc_network = self.get_resource()
        vdc_network.set('name', name)
        if description is not None:
            vdc_network.Description = E.Description(description)
        if is_shared is not None:
            vdc_network.IsShared = E.IsShared(is_shared)
        return self.client.put_linked_resource(
            self.resource, RelationType.EDIT, EntityType.ORG_VDC_NETWORK.value,
            vdc_network)

    def add_static_ip_pool(self, ip_ranges_param):
        """Add static IP pool for org vdc network.

        :param list ip_ranges_param: list of ip ranges.
            For ex: [2.3.3.2-2.3.3.10]

        :return: object containing EntityType.TASK XML data representing the
            asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        vdc_network = self.get_resource()
        ip_scope = vdc_network.Configuration.IpScopes.IpScope
        if not hasattr(ip_scope, 'IpRanges'):
            ip_scope.append(E.IpRanges())

        ip_ranges_list = ip_scope.IpRanges
        for ip_range in ip_ranges_param:
            ip_range_arr = ip_range.split('-')
            if len(ip_range_arr) > 1:
                start_address = ip_range_arr[0]
                end_address = ip_range_arr[1]
            elif len(ip_range_arr) == 1:
                #if provided parameter is just start Address then it will
                # consider endAddress as same.
                start_address = ip_range_arr[0]
                end_address = ip_range_arr[0]
            ip_range_tag = E.IpRange()
            ip_range_tag.append(E.StartAddress(
                start_address))
            ip_range_tag.append(E.EndAddress(
                end_address))
            ip_ranges_list.append(ip_range_tag)

        return self.client.put_linked_resource(
            self.resource, RelationType.EDIT, EntityType.ORG_VDC_NETWORK.value,
            vdc_network)
