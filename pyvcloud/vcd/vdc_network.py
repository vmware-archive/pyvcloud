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
from pyvcloud.vcd.client import VAppPowerStatus
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
        self.admin_resource = None

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

    def get_admin_resource(self):
        """Fetches the XML representation of the admin org vdc network.

        Will serve cached response if possible.

        :return: object containing EntityType.ORG_VDC_NETWORK XML data
        representing the org vdc.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.admin_resource is None:
            self.reload_admin()
        return self.admin_resource

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

    def reload_admin(self):
        """Reloads the admin resource representation of the org vdc network.

        This method should be called in between two method invocations on the
        Admin Org Vdc Network object, if the former call changes the
        representation of the admin org vdc network in vCD.
        """
        self.admin_resource = self.client.get_resource(self.href_admin)
        if self.admin_resource is not None:
            self.href_admin = self.admin_resource.get('href')

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

    def add_static_ip_pool_and_dns(self,
                                   ip_ranges_param=None,
                                   primary_dns_ip=None,
                                   secondary_dns_ip=None,
                                   dns_suffix=None):
        """Add static IP pool and DNS for org vdc network.

        :param list ip_ranges_param: list of ip ranges.
            For ex: [2.3.3.2-2.3.3.10]

        :param str primary_dns_ip: IP address of primary DNS server.

        :param str secondary_dns_ip: IP address of secondary DNS Server.

        :param str dns_suffix: DNS suffix.

        :return: object containing EntityType.TASK XML data representing the
            asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if ip_ranges_param is None and primary_dns_ip is None and \
                secondary_dns_ip is None and dns_suffix is None:
            raise InvalidParameterException("All input params can't be None "
                                            "or empty")
        vdc_network = self.get_resource()
        ip_scopes = ip_scope = vdc_network.Configuration.IpScopes
        ip_scope = ip_scopes.IpScope
        ip_scopes.remove(ip_scope)

        ip_scopes.append(E.IpScope())
        ip_scope_new = ip_scopes.IpScope
        ip_scope_new.IsInherited = ip_scope.IsInherited
        ip_scope_new.Gateway = ip_scope.Gateway
        ip_scope_new.Netmask = ip_scope.Netmask
        ip_scope_new.SubnetPrefixLength = ip_scope.SubnetPrefixLength

        if primary_dns_ip is not None:
            ip_scope_new.append(E.Dns1(primary_dns_ip))
        elif hasattr(ip_scope, 'Dns1'):
            ip_scope_new.append(ip_scope.Dns1)

        if secondary_dns_ip is not None:
            ip_scope_new.append(E.Dns2(secondary_dns_ip))
        elif hasattr(ip_scope, 'Dns2'):
            ip_scope_new.append(ip_scope.Dns2)

        if dns_suffix is not None:
            ip_scope_new.append(E.DnsSuffix(dns_suffix))
        elif hasattr(ip_scope, 'DnsSuffix'):
            ip_scope_new.append(ip_scope.DnsSuffix)

        if hasattr(ip_scope, 'IsEnabled'):
            ip_scope_new.append(ip_scope.IsEnabled)

        if hasattr(ip_scope, 'IpRanges'):
            ip_scope_new.append(ip_scope.IpRanges)

        if ip_ranges_param is not None and len(ip_ranges_param) > 0:
            if not hasattr(ip_scope, 'IpRanges'):
                ip_scope_new.append(E.IpRanges())

            ip_ranges_list = ip_scope_new.IpRanges
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
                ip_range_tag.append(E.StartAddress(start_address))
                ip_range_tag.append(E.EndAddress(end_address))
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

    def remove_static_ip_pool(self, ip_range_param):
        """Remove static IP pool of org vdc network.

        :param str ip_range_param: ip range. For ex: 2.3.3.2-2.3.3.10

        :return: object containing EntityType.TASK XML data representing the
            asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        vdc_network = self.get_resource()
        ip_scope = vdc_network.Configuration.IpScopes.IpScope
        if not hasattr(ip_scope, 'IpRanges'):
            raise OperationNotSupportedException('No IP range found.')

        for ip_range in ip_scope.IpRanges.IpRange:
            if (ip_range.StartAddress + '-' +
                    ip_range.EndAddress) == ip_range_param:
                ip_scope.IpRanges.remove(ip_range)

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
        metadata = Metadata(
            client=self.client, resource=self.get_all_metadata())
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
        metadata = Metadata(
            client=self.client, resource=self.get_all_metadata())
        return metadata.set_metadata(
            key=key,
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
        metadata = Metadata(
            client=self.client, resource=self.get_all_metadata())
        return metadata.remove_metadata(
            key=key, domain=domain, use_admin_endpoint=True)

    def list_allocated_ip_address(self):
        """List allocated ip address of org vDC network.

        :return: List where each entry is a dictionary containing allocated IP
            address, deploy status and type.
            For example: [{'IP Address': '10.20.30.1', 'Is Deployed': 'true',
            'Type': 'vsmAllocated'}]
        :rtype: list
        """
        allocated_ip_addresses = self.client.get_linked_resource(
            self.get_resource(), RelationType.DOWN,
            EntityType.ALLOCATED_NETWORK_ADDRESS.value)
        result = []
        for ip_address in allocated_ip_addresses.IpAddress:
            result.append({
                'IP Address': ip_address.IpAddress,
                'Is Deployed': ip_address.get('isDeployed'),
                'Type': ip_address.get('allocationType')
            })
        return result

    def list_connected_vapps(self, filter=None):
        """List connected vApps.

        :param str filter: filter to fetch the selected vApp, e.g., name==vApp*
        :return: list of connected vApps
        :rtype: list
        """
        vapp_name_list = []
        if (self.client.is_sysadmin()):
            vdc = self.client.get_linked_resource(self.get_resource(),
                                                  RelationType.UP,
                                                  EntityType.VDC_ADMIN.value)
        else:
            vdc = self.client.get_linked_resource(
                self.get_resource(), RelationType.UP, EntityType.VDC.value)

        for entity in vdc.ResourceEntities.ResourceEntity:
            if entity.get('type') == EntityType.VAPP.value:
                vapp = self.client.get_resource(entity.get('href'))
                if hasattr(vapp, 'NetworkConfigSection'):
                    network_name = vapp.NetworkConfigSection.NetworkConfig.get(
                        'networkName')
                    if network_name == self.name:
                        vapp_name_list.append({
                            'Name': vapp.get('name'),
                            'Status': VAppPowerStatus(vapp.get('status')).name
                        })
        return vapp_name_list

    def convert_to_sub_interface(self):
        """Convert to sub interface.

        :return: an object of type EntityType.TASK XML which represents
            the asynchronous task that is converting to sub-interface.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        self.get_admin_resource()

        return self.client.post_linked_resource(
            self.admin_resource,
            RelationType.VDC_ROUTED_CONVERT_TO_SUB_INTERFACE, None, None)

    def convert_to_internal_interface(self):
        """Convert to internal interface.

        :return: an object of type EntityType.TASK XML which represents
            the asynchronous task that is converting to sub-interface.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        self.get_admin_resource()

        return self.client.post_linked_resource(
            self.admin_resource,
            RelationType.VDC_ROUTED_CONVERT_TO_INTERNAL_INTERFACE, None, None)

    def convert_to_distributed_interface(self):
        """Convert to distributed interface.

        :return: an object of type EntityType.TASK XML which represents
            the asynchronous task that is converting to sub-interface.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        self.get_admin_resource()

        return self.client.post_linked_resource(
            self.admin_resource,
            RelationType.VDC_ROUTED_CONVERT_TO_DISTRIBUTED_INTERFACE, None,
            None)
