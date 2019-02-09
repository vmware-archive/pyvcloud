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

from pyvcloud.vcd.client import E
from pyvcloud.vcd.client import E_VMEXT
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import QueryResultFormat
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.client import ResourceType
from pyvcloud.vcd.exceptions import EntityNotFoundException
from pyvcloud.vcd.exceptions import InvalidParameterException
from pyvcloud.vcd.gateway import Gateway
from pyvcloud.vcd.platform import Platform
from pyvcloud.vcd.pvdc import PVDC
from pyvcloud.vcd.utils import get_admin_href


class ExternalNetwork(object):
    def __init__(self, client, name=None, href=None, resource=None):
        """Constructor for External Network objects.

        :param pyvcloud.vcd.client.Client client: the client that will be used
            to make REST calls to vCD.
        :param str name: name of the entity.
        :param str href: URI of the entity.
        :param lxml.objectify.ObjectifiedElement resource: object containing
            EntityType.EXTERNAL_NETWORK XML data representing the external
            network.
        """
        self.client = client
        self.name = name
        if href is None and resource is None:
            raise InvalidParameterException(
                "External network initialization failed as arguments are "
                "either invalid or None")
        self.href = href
        self.resource = resource
        if resource is not None:
            self.name = resource.get('name')
            self.href = resource.get('href')
        self.href_admin = get_admin_href(self.href)

    def get_resource(self):
        """Fetches the XML representation of the external network from vCD.

        Will serve cached response if possible.

        :return: object containing EntityType.EXTERNAL_NETWORK XML data
        representing the external network.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.reload()
        return self.resource

    def reload(self):
        """Reloads the resource representation of the external network.

        This method should be called in between two method invocations on the
        external network object, if the former call changes the representation
        of the external network in vCD.
        """
        self.resource = self.client.get_resource(self.href)
        if self.resource is not None:
            self.name = self.resource.get('name')
            self.href = self.resource.get('href')

    def add_subnet(self,
                   name,
                   gateway_ip,
                   netmask,
                   ip_ranges,
                   primary_dns_ip=None,
                   secondary_dns_ip=None,
                   dns_suffix=None):
        """Add subnet to an external network.

        :param str name: Name of external network.

        :param str gateway_ip: IP address of the gateway of the new network.

        :param str netmask: Netmask of the gateway.

        :param list ip_ranges: list of IP ranges used for static pool
            allocation in the network. For example, [192.168.1.2-192.168.1.49,
            192.168.1.100-192.168.1.149].

        :param str primary_dns_ip: IP address of primary DNS server.

        :param str secondary_dns_ip: IP address of secondary DNS Server.

        :param str dns_suffix: DNS suffix.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.reload()

        platform = Platform(self.client)
        ext_net = platform.get_external_network(name)
        config = ext_net['{' + NSMAP['vcloud'] + '}Configuration']
        ip_scopes = config.IpScopes

        ip_scope = E.IpScope()
        ip_scope.append(E.IsInherited(False))
        ip_scope.append(E.Gateway(gateway_ip))
        ip_scope.append(E.Netmask(netmask))
        if primary_dns_ip is not None:
            ip_scope.append(E.Dns1(primary_dns_ip))
        if secondary_dns_ip is not None:
            ip_scope.append(E.Dns2(secondary_dns_ip))
        if dns_suffix is not None:
            ip_scope.append(E.DnsSuffix(dns_suffix))
        ip_scope.append(E.IsEnabled(True))
        e_ip_ranges = E.IpRanges()
        for ip_range in ip_ranges:
            e_ip_range = E.IpRange()
            ip_range_token = ip_range.split('-')
            e_ip_range.append(E.StartAddress(ip_range_token[0]))
            e_ip_range.append(E.EndAddress(ip_range_token[1]))
            e_ip_ranges.append(e_ip_range)
        ip_scope.append(e_ip_ranges)
        ip_scopes.append(ip_scope)

        return self.client.put_linked_resource(
            ext_net,
            rel=RelationType.EDIT,
            media_type=EntityType.EXTERNAL_NETWORK.value,
            contents=ext_net)

    def enable_subnet(self, gateway_ip, is_enabled=None):
        """Enable subnet of an external network.

        :param str gateway_ip: IP address of the gateway of external network.

        :param bool is_enabled: flag to enable/disable the subnet

        :rtype: lxml.objectify.ObjectifiedElement
        """
        ext_net = self.client.get_resource(self.href)

        config = ext_net['{' + NSMAP['vcloud'] + '}Configuration']
        ip_scopes = config.IpScopes

        if is_enabled is not None:
            for ip_scope in ip_scopes.IpScope:
                if ip_scope.Gateway == gateway_ip:
                    if hasattr(ip_scope, 'IsEnabled'):
                        ip_scope['IsEnabled'] = E.IsEnabled(is_enabled)
                        return self.client. \
                            put_linked_resource(ext_net, rel=RelationType.EDIT,
                                                media_type=EntityType.
                                                EXTERNAL_NETWORK.value,
                                                contents=ext_net)
        return ext_net

    def add_ip_range(self, gateway_ip, ip_ranges):
        """Add new ip range into a subnet of an external network.

        :param str gateway_ip: IP address of the gateway of external network.

        :param list ip_ranges: list of IP ranges used for static pool
            allocation in the network. For example, [192.168.1.2-192.168.1.49,
            192.168.1.100-192.168.1.149]

        :rtype: lxml.objectify.ObjectifiedElement
        """
        ext_net = self.client.get_resource(self.href)

        config = ext_net['{' + NSMAP['vcloud'] + '}Configuration']
        ip_scopes = config.IpScopes

        for ip_scope in ip_scopes.IpScope:
            if ip_scope.Gateway == gateway_ip:
                existing_ip_ranges = ip_scope.IpRanges
                break

        for range in ip_ranges:
            range_token = range.split('-')
            e_ip_range = E.IpRange()
            e_ip_range.append(E.StartAddress(range_token[0]))
            e_ip_range.append(E.EndAddress(range_token[1]))
            existing_ip_ranges.append(e_ip_range)

        return self.client. \
            put_linked_resource(ext_net, rel=RelationType.EDIT,
                                media_type=EntityType.
                                EXTERNAL_NETWORK.value,
                                contents=ext_net)

    def modify_ip_range(self, gateway_ip, old_ip_range, new_ip_range):
        """Modify ip range of a subnet in external network.

        :param str gateway_ip: IP address of the gateway of external
             network.
        :param str old_ip_range: existing ip range present in the static pool
             allocation in the network. For example, [192.168.1.2-192.168.1.20]

        :param str new_ip_range: new ip range to replace the existing ip range
             present in the static pool allocation in the network.

        :return: object containing vmext:VMWExternalNetwork XML element that
             representing the external network.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.reload()
        ext_net = self.resource
        old_ip_addrs = old_ip_range.split('-')
        new_ip_addrs = new_ip_range.split('-')
        config = ext_net['{' + NSMAP['vcloud'] + '}Configuration']
        ip_scopes = config.IpScopes
        ip_range_found = False

        for ip_scope in ip_scopes.IpScope:
            if ip_scope.Gateway == gateway_ip:
                for exist_ip_range in ip_scope.IpRanges.IpRange:
                    if exist_ip_range.StartAddress == \
                            old_ip_addrs[0] and \
                            exist_ip_range.EndAddress \
                            == old_ip_addrs[1]:
                        exist_ip_range['StartAddress'] = \
                            E.StartAddress(new_ip_addrs[0])
                        exist_ip_range['EndAddress'] = \
                            E.EndAddress(new_ip_addrs[1])
                        ip_range_found = True
                        break

        if not ip_range_found:
            raise EntityNotFoundException(
                'IP Range \'%s\' not Found' % old_ip_range)

        return self.client. \
            put_linked_resource(ext_net, rel=RelationType.EDIT,
                                media_type=EntityType.
                                EXTERNAL_NETWORK.value,
                                contents=ext_net)

    def delete_ip_range(self, gateway_ip, ip_ranges):
        """Delete ip range of a subnet in external network.

        :param str gateway_ip: IP address of the gateway of external
             network.

        :param list ip_ranges: existing ip range present in the static pool
             allocation in the network to be deleted.
             For example, [192.168.1.2-192.168.1.20]

        :return: object containing vmext:VMWExternalNetwork XML element that
             representing the external network.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.reload()
        ext_net = self.resource

        config = ext_net['{' + NSMAP['vcloud'] + '}Configuration']
        ip_scopes = config.IpScopes

        for ip_scope in ip_scopes.IpScope:
            if ip_scope.Gateway == gateway_ip:
                exist_ip_ranges = ip_scope.IpRanges
                self.__remove_ip_range_elements(exist_ip_ranges, ip_ranges)

        return self.client. \
            put_linked_resource(ext_net, rel=RelationType.EDIT,
                                media_type=EntityType.
                                EXTERNAL_NETWORK.value,
                                contents=ext_net)

    def attach_port_group(self, vim_server_name, port_group_name):
        """Attach a portgroup to an external network.

        :param str vc_name: name of vc where portgroup is present.
        :param str pg_name: name of the portgroup to be attached to
             external network.

        return: object containing vmext:VMWExternalNetwork XML element that
             representing the external network.
        :rtype: lxml.objectify.ObjectifiedElement
        """
        ext_net = self.get_resource()
        platform = Platform(self.client)

        if not vim_server_name or not port_group_name:
            raise InvalidParameterException(
                "Either vCenter Server name is none or portgroup name is none")

        vc_record = platform.get_vcenter(vim_server_name)
        vc_href = vc_record.get('href')
        pg_moref_types = \
            platform.get_port_group_moref_types(vim_server_name,
                                                port_group_name)

        if hasattr(ext_net, '{' + NSMAP['vmext'] + '}VimPortGroupRef'):
            vim_port_group_refs = E_VMEXT.VimPortGroupRefs()
            vim_object_ref1 = self.__create_vimobj_ref(
                vc_href, pg_moref_types[0], pg_moref_types[1])

            # Create a new VimObjectRef using vc href, portgroup moref and type
            # from existing VimPortGroupRef. Add the VimObjectRef to
            # VimPortGroupRefs and then delete VimPortGroupRef
            # from external network.
            vim_pg_ref = ext_net['{' + NSMAP['vmext'] + '}VimPortGroupRef']
            vc2_href = vim_pg_ref.VimServerRef.get('href')
            vim_object_ref2 = self.__create_vimobj_ref(
                vc2_href, vim_pg_ref.MoRef.text, vim_pg_ref.VimObjectType.text)

            vim_port_group_refs.append(vim_object_ref1)
            vim_port_group_refs.append(vim_object_ref2)
            ext_net.remove(vim_pg_ref)
            ext_net.append(vim_port_group_refs)
        else:
            vim_port_group_refs = \
                ext_net['{' + NSMAP['vmext'] + '}VimPortGroupRefs']
            vim_object_ref1 = self.__create_vimobj_ref(
                vc_href, pg_moref_types[0], pg_moref_types[1])
            vim_port_group_refs.append(vim_object_ref1)

        return self.client. \
            put_linked_resource(ext_net, rel=RelationType.EDIT,
                                media_type=EntityType.
                                EXTERNAL_NETWORK.value,
                                contents=ext_net)

    def __create_vimobj_ref(self, vc_href, pg_moref, pg_type):
        """Creates the VimObjectRef."""
        vim_object_ref = E_VMEXT.VimObjectRef()
        vim_object_ref.append(E_VMEXT.VimServerRef(href=vc_href))
        vim_object_ref.append(E_VMEXT.MoRef(pg_moref))
        vim_object_ref.append(E_VMEXT.VimObjectType(pg_type))

        return vim_object_ref

    def detach_port_group(self, vim_server_name, port_group_name):
        """Detach a portgroup from an external network.

        :param str vim_server_name: name of vim server where
        portgroup is present.
        :param str port_group_name: name of the portgroup to be detached from
             external network.

        return: object containing vmext:VMWExternalNetwork XML element that
             representing the external network.
        :rtype: lxml.objectify.ObjectifiedElement
        """
        ext_net = self.get_resource()
        platform = Platform(self.client)

        if not vim_server_name or not port_group_name:
            raise InvalidParameterException(
                "Either vCenter Server name is none or portgroup name is none")

        vc_record = platform.get_vcenter(vim_server_name)
        vc_href = vc_record.get('href')
        if hasattr(ext_net, 'VimPortGroupRefs'):
            pg_moref_types = \
                platform.get_port_group_moref_types(vim_server_name,
                                                    port_group_name)
        else:
            raise \
                InvalidParameterException("External network"
                                          " has only one port group")

        vim_port_group_refs = ext_net.VimPortGroupRefs
        vim_obj_refs = vim_port_group_refs.VimObjectRef
        for vim_obj_ref in vim_obj_refs:
            if vim_obj_ref.VimServerRef.get('href') == vc_href \
                    and vim_obj_ref.MoRef == pg_moref_types[0] \
                    and vim_obj_ref.VimObjectType == pg_moref_types[1]:
                vim_port_group_refs.remove(vim_obj_ref)

        return self.client. \
            put_linked_resource(ext_net, rel=RelationType.EDIT,
                                media_type=EntityType.
                                EXTERNAL_NETWORK.value,
                                contents=ext_net)

    def list_provider_vdc(self, filter=None):
        """List associated provider vdcs.

        :param str filter: filter to fetch the selected pvdc, e.g., name==pvdc*
        :return: list of associated provider vdcs
        :rtype: list
        """
        pvdc_name_list = []
        query = self.client.get_typed_query(
            ResourceType.PROVIDER_VDC.value,
            query_result_format=QueryResultFormat.RECORDS,
            qfilter=filter)
        records = query.execute()
        if records is None:
            raise EntityNotFoundException('No Provider Vdc found associated')
        for record in records:
            href = record.get('href')
            pvdc_name = self._get_provider_vdc_name_for_provided_ext_nw(href)
            if pvdc_name is not None:
                pvdc_name_list.append(pvdc_name)
        return pvdc_name_list

    def _get_provider_vdc_name_for_provided_ext_nw(self, pvdc_href):
        pvdc = PVDC(self.client, href=pvdc_href)
        pvdc_resource = pvdc.get_resource()
        if not hasattr(pvdc_resource, "AvailableNetworks") and hasattr(
                pvdc_resource.AvailableNetworks, "Network"):
            return None
        networks = pvdc_resource.AvailableNetworks.Network
        for network in networks:
            pvdc_ext_nw_name = network.get("name")
            if pvdc_ext_nw_name == self.name:
                return pvdc_resource.get('name')
        return None

    def __remove_ip_range_elements(self, existing_ip_ranges, ip_ranges):
        """Removes the given IP ranges from existing IP ranges.

        :param existing_ip_ranges: existing IP range present from the subnet
               pool.

        :param list ip_ranges: IP ranges that needs to be removed.
        """
        for exist_range in existing_ip_ranges.IpRange:
            for remove_range in ip_ranges:
                address = remove_range.split('-')
                start_addr = address[0]
                end_addr = address[1]
                if start_addr == exist_range.StartAddress and \
                        end_addr == exist_range.EndAddress:
                    existing_ip_ranges.remove(exist_range)

    def list_extnw_gateways(self, filter=None):
        """List associated gateways.

        :param str filter: filter to fetch the selected gateway, e.g.,
        name==gateway*
        :return: list of associated gateways
        :rtype: list
        """
        gateway_name_list = []
        records = self.__execute_gateway_query_api(filter)
        for record in records:
            href = record.get('href')
            gateway_name = self._get_gateway_name_for_provided_ext_nw(href)
            if gateway_name is not None:
                gateway_name_list.append(gateway_name)
        return gateway_name_list

    def _get_gateway_name_for_provided_ext_nw(self, gateway_href):
        gateway_resource = self.__get_gateway_resource(gateway_href)
        for gw_inf in gateway_resource.Configuration.GatewayInterfaces. \
                GatewayInterface:
            if gw_inf.InterfaceType == "uplink" and gw_inf.Name == self.name:
                return gateway_resource.get('name')
        return None

    def list_allocated_ip_address(self, filter=None):
        """List allocated ip address of gateways.

        :param str filter: filter to fetch the selected gateway, e.g.,
        name==gateway*
        :return: dict allocated ip address of associated gateways
        :rtype: dict
        """
        gateway_name_allocated_ip_dict = {}
        records = self.__execute_gateway_query_api(filter)
        for record in records:
            href = record.get('href')
            gateway_entry = self. \
                _get_gateway_allocated_ip_for_provided_ext_nw(href)
            if gateway_entry is not None:
                gateway_name_allocated_ip_dict[gateway_entry[0]] = \
                    gateway_entry[1]
        return gateway_name_allocated_ip_dict

    def __execute_gateway_query_api(self, filter=None):
        query = self.client.get_typed_query(
            ResourceType.EDGE_GATEWAY.value,
            query_result_format=QueryResultFormat.RECORDS,
            qfilter=filter)
        query_records = query.execute()
        if query_records is None:
            raise EntityNotFoundException('No Gateway found associated')
        return query_records

    def _get_gateway_allocated_ip_for_provided_ext_nw(self, gateway_href):
        gateway_allocated_ip = []
        gateway_resource = self.__get_gateway_resource(gateway_href)
        for gw_inf in gateway_resource.Configuration.GatewayInterfaces. \
                GatewayInterface:
            if gw_inf.InterfaceType == "uplink" and gw_inf.Name == self.name:
                gateway_allocated_ip.append(gateway_resource.get('name'))
                gateway_allocated_ip. \
                    append(gw_inf.SubnetParticipation.IpAddress)
                return gateway_allocated_ip
        return None

    def list_gateway_ip_suballocation(self, filter=None):
        """List gateway ip sub allocation.

        :param str filter: filter to fetch the selected gateway, e.g.,
        name==gateway*
        :return: dict gateway ip sub allocation
        :rtype: dict
        """
        gateway_name_sub_allocated_ip_dict = {}
        records = self.__execute_gateway_query_api(filter)
        for record in records:
            href = record.get('href')
            gateway_entry = self. \
                _get_gateway_sub_allocated_ip_for_provided_ext_nw(href)
            if gateway_entry is not None:
                gateway_name_sub_allocated_ip_dict[gateway_entry[0]] = \
                    gateway_entry[1]
        return gateway_name_sub_allocated_ip_dict

    def _get_gateway_sub_allocated_ip_for_provided_ext_nw(self, gateway_href):
        gateway_sub_allocated_ip = []
        allocation_range = ''
        gateway_resource = self.__get_gateway_resource(gateway_href)
        for gw_inf in gateway_resource.Configuration.GatewayInterfaces. \
                GatewayInterface:
            if gw_inf.InterfaceType == "uplink" and gw_inf.Name == self.name:
                if hasattr(gw_inf.SubnetParticipation, 'IpRanges'):
                    for ip_range in gw_inf.SubnetParticipation. \
                            IpRanges.IpRange:
                        start_address = ip_range.StartAddress
                        end_address = ip_range.EndAddress
                        allocation_range += \
                            start_address + '-' + end_address + ','
            gateway_sub_allocated_ip.append(gateway_resource.get('name'))
            gateway_sub_allocated_ip.append(allocation_range)
            return gateway_sub_allocated_ip
        return None

    def __get_gateway_resource(self, gateway_href):
        gateway = Gateway(self.client, href=gateway_href)
        return gateway.get_resource()

    def list_associated_direct_org_vdc_networks(self, filter=None):
        """List associated direct org vDC networks.

        :param str filter: filter to fetch the direct org vDC network,
        e.g., connectedTo==Ext*
        :return: list of direct org vDC networks
        :rtype: list
        :raises: EntityNotFoundException: if any direct org vDC network
         cannot be found.
        """
        query_filter = 'connectedTo==' + self.name
        if filter:
            query_filter += ';' + filter
        query = self.client.get_typed_query(
            ResourceType.ORG_VDC_NETWORK.value,
            qfilter=query_filter,
            query_result_format=QueryResultFormat.RECORDS)
        records = list(query.execute())

        direct_ovdc_network_names = [record.get('name') for record in records]
        return direct_ovdc_network_names

    def list_vsphere_network(self, filter=None):
        """List associated vSphere Networks.

        :param str filter: filter to fetch the vSphere Networks,
        e.g., networkName==Ext*
        :return: list of associated vSphere networks
        e.g.
        [{'vCenter': 'vc1', 'Name': 'test-dvpg'}]
        :rtype: list
        """
        out_list = []
        query_filter = 'networkName==' + self.name
        if filter:
            query_filter += ';' + filter
        query = self.client.get_typed_query(
            ResourceType.PORT_GROUP.value,
            query_result_format=QueryResultFormat.RECORDS,
            qfilter=query_filter)
        records = query.execute()

        for record in records:
            vSphere_network_list = dict()
            vSphere_network_list['vCenter'] = record.get('vcName')
            vSphere_network_list['Name'] = record.get('name')
            out_list.append(vSphere_network_list)
        return out_list
