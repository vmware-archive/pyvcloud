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
from pyvcloud.vcd.client import MetadataDomain
from pyvcloud.vcd.client import MetadataValueType
from pyvcloud.vcd.client import MetadataVisibility
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.exceptions import InvalidParameterException
from pyvcloud.vcd.exceptions import OperationNotSupportedException
from pyvcloud.vcd.metadata import Metadata
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
                # if provided parameter is just start Address then it will
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

    def modify_static_ip_pool(self, ip_range_param, new_ip_range_param):
        """Modify static IP pool of org vdc network.

        :param str ip_range_param: ip range. For ex: 2.3.3.2-2.3.3.10

        :param str new_ip_range_param: new ip range. For ex: 2.3.3.11-2.3.3.20

        :return: object containing EntityType.TASK XML data representing the
            asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        vdc_network = self.get_resource()
        ip_scope = vdc_network.Configuration.IpScopes.IpScope
        if not hasattr(ip_scope, 'IpRanges'):
            raise OperationNotSupportedException('No IP range found.')
        ip_ranges_list = ip_scope.IpRanges.IpRange

        for ip_range in ip_ranges_list:
            ip_range_arr = ip_range_param.split('-')
            new_ip_range_arr = new_ip_range_param.split('-')
            if len(ip_range_arr) <= 1 or len(new_ip_range_arr) <= 1:
                raise InvalidParameterException('Input params should be in '
                                                'x.x.x.x-y.y.y.y')
            if (ip_range.StartAddress + '-' + ip_range.EndAddress) != \
                    ip_range_param:
                continue
            new_start_address = new_ip_range_arr[0]
            new_end_address = new_ip_range_arr[1]

            ip_range.StartAddress = E.StartAddress(new_start_address)
            ip_range.EndAddress = E.StartAddress(new_end_address)

        return self.client.put_linked_resource(
            self.resource, RelationType.EDIT, EntityType.ORG_VDC_NETWORK.value,
            vdc_network)

    def get_all_metadata(self):
        """Fetch all metadata entries of the org vdc network.

        :return: an object containing EntityType.METADATA XML data which
            represents the metadata entries associated with the org vdc
            network.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        self.get_resource()
        return self.client.get_linked_resource(
            self.resource, RelationType.DOWN, EntityType.METADATA.value)

    def get_metadata_value(self, key, domain=MetadataDomain.GENERAL):
        """Fetch the metadata value identified by the domain and key.

        :param str key: key of the metadata to be fetched.
        :param client.MetadataDomain domain: domain of the value to be fetched.

        :return: an object containing EntityType.METADATA_VALUE XML data which
            represents the metadata value.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        metadata = Metadata(client=self.client,
                            resource=self.get_all_metadata())
        return metadata.get_metadata_value(key, domain)

    def set_metadata(self,
                     key,
                     value,
                     domain=MetadataDomain.GENERAL,
                     visibility=MetadataVisibility.READ_WRITE,
                     metadata_value_type=MetadataValueType.STRING):
        """Add a metadata entry to the org vdc network.

        Only admins can perform this operation. If an entry with the same key
        exists, it will be updated with the new value.

        :param str key: an arbitrary key name. Length cannot exceed 256 UTF-8
            characters.
        :param str value: value of the metadata entry
        :param client.MetadataDomain domain: domain where the new entry would
            be put.
        :param client.MetadataVisibility visibility: visibility of the metadata
            entry.
        :param client.MetadataValueType metadata_value_type:

        :return: an object of type EntityType.TASK XML which represents
            the asynchronous task that is updating the metadata on the org vdc
            network.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        metadata = Metadata(client=self.client,
                            resource=self.get_all_metadata())
        return metadata.set_metadata(key=key,
                                     value=value,
                                     domain=domain,
                                     visibility=visibility,
                                     metadata_value_type=metadata_value_type,
                                     use_admin_endpoint=True)

    def remove_metadata(self, key, domain=MetadataDomain.GENERAL):
        """Remove a metadata entry from the org vdc network.

        Only admins can perform this operation.

        :param str key: key of the metadata to be removed.
        :param client.MetadataDomain domain: domain of the entry to be removed.

        :return: an object of type EntityType.TASK XML which represents
            the asynchronous task that is deleting the metadata on the org vdc
            network.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: AccessForbiddenException: If there is no metadata entry
            corresponding to the key provided.
        """
        metadata = Metadata(client=self.client,
                            resource=self.get_all_metadata())
        return metadata.remove_metadata(key=key,
                                        domain=domain,
                                        use_admin_endpoint=True)
