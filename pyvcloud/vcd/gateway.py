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
from pyvcloud.vcd.client import GatewayBackingConfigType
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.exceptions import AlreadyExistsException
from pyvcloud.vcd.exceptions import EntityNotFoundException
from pyvcloud.vcd.exceptions import InvalidParameterException
from pyvcloud.vcd.platform import Platform
from pyvcloud.vcd.utils import get_admin_href
from pyvcloud.vcd.utils import netmask_to_cidr_prefix_len


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
        if href is None:
            raise InvalidParameterException(
                "Gateway initialization failed as arguments are either "
                "invalid or None")
        self.href = href
        if resource is None:
            self.resource = None
            self.get_resource()

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

    def convert_to_advanced(self):
        """Convert to advanced gateway.

        :return: object containing EntityType.TASK XML data representing the
            asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement

        """
        if self.resource is None:
            self.reload()

        return self.client.post_linked_resource(
            self.resource, RelationType.CONVERT_TO_ADVANCED_GATEWAY, None,
            None)

    def enable_distributed_routing(self, enable=True):
        """Enable Distributed Routing.

        :param bool enable: True if user want to enable else False.

        :return: object containing EntityType.TASK XML data
            representing the asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.reload()
        gateway = self.resource
        current_dr_status = gateway.Configuration.DistributedRoutingEnabled
        if enable == current_dr_status:
            return
        gateway.Configuration.DistributedRoutingEnabled = \
            E.DistributedRoutingEnabled(enable)
        return self.client.put_linked_resource(
            self.resource, RelationType.EDIT, EntityType.EDGE_GATEWAY.value,
            gateway)

    def modify_form_factor(self, gateway_type):
        """Modify form factor.

        This operation can be performed by only System Administrators.

        :param str gateway_type: gateway config type, possible values
            are compact/full/full4/x-large.

        :return: object containing EntityType.TASK XML data representing the
            asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: InvalidParameterException: if provided gateway config type
            is not from list compact/full/full4/x-large.
        """
        self.get_resource()
        try:
            GatewayBackingConfigType.__getitem__(gateway_type)
        except ValueError:
            raise InvalidParameterException(
                'Provided %s is not valid. It '
                'should be from allowed list '
                'compact/full/full4/x-large' % gateway_type)
        gateway_form_factor = E.EdgeGatewayFormFactor()
        gateway_form_factor.append(E.gatewayType(gateway_type))
        return self.client.post_linked_resource(
            self.resource, RelationType.MODIFY_FORM_FACTOR,
            EntityType.EDGE_GATEWAY_FORM_FACTOR.value, gateway_form_factor)

    def list_external_network_ip_allocations(self):
        """List external network ip allocations of the gateway.

        This operation can be performed by System/Org Administrators.

        :return: a dictionary that maps external network name to list of ip
            addresses. Ex: {'extnw1': ['10.10.10.2'...]}

        :rtype: dict
        """
        gateway = self.get_resource()
        out = {}
        for inf in gateway.Configuration.GatewayInterfaces.GatewayInterface:
            if inf.InterfaceType.text == 'uplink':
                ips = out.setdefault(inf.Name.text, [])
                ips.append(inf.SubnetParticipation.IpAddress.text)
        return out

    def redeploy(self):
        """Redeploy the gateway.

        :return: object containing EntityType.TASK XML data representing the
            asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.reload()

        return self.client.post_linked_resource(
            self.resource, RelationType.GATEWAY_REDEPLOY, None, None)

    def sync_syslog_settings(self):
        """Sync syslog settings of the gateway.

        :return: object containing EntityType.TASK XML data representing the
            asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.reload()

        return self.client.post_linked_resource(
            self.resource, RelationType.GATEWAY_SYNC_SYSLOG_SETTINGS, None,
            None)

    def list_configure_ip_settings(self):
        """List all gateway's configure ip settings in the current vdc.

        :return:  a list of dictionary that has gateway's configure ip settings
            Ex: [{'external_network':
            'external_network_de99a4e2-f6d8-11e8-9e0c-9061ae543719',
            'gateway': ['10.20.30.1/24'], 'ip_address': ['10.20.30.2']}]

        :rtype: list

        """
        out_list = []
        gateway = self.get_resource()
        for gatewayinf in \
                gateway.Configuration.GatewayInterfaces.GatewayInterface:
            ipconfigsettings = dict()
            ipconfigsettings['external_network'] = gatewayinf.Name.text
            gatewayips = ipconfigsettings.setdefault('gateway', [])
            ips = ipconfigsettings.setdefault('ip_address', [])
            for subnetpart in gatewayinf.SubnetParticipation:
                if hasattr(subnetpart, 'SubnetPrefixLength'):
                    gatewayips.append(subnetpart.Gateway.text + '/' +
                                      subnetpart.SubnetPrefixLength.text)
                else:
                    gatewayips.append(subnetpart.Gateway.text + '/' +
                                      str(netmask_to_cidr_prefix_len(
                                          subnetpart.Gateway.text,
                                          subnetpart.Netmask.text)))
                ips.append(subnetpart.IpAddress.text)
            out_list.append(ipconfigsettings)
        return out_list

    def _create_gateway_interface(self, ext_nw, interface_type):
        """Creates gateway interface object connected to given network.

        :param lxml.objectify.ObjectifiedElement ext_nw: external network.

        :param str interface_type: interface type of the gateway.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        gateway_interface_param = E.GatewayInterface()
        gateway_interface_param.append(E.Name(ext_nw.get('name')))
        gateway_interface_param.append(E.DisplayName(ext_nw.get('name')))
        gateway_interface_param.append(E.Network(href=ext_nw.get('href')))
        gateway_interface_param.append(E.InterfaceType(interface_type))
        return gateway_interface_param

    def _get_external_network(self, name):
        """Gets external network object by given name.

        :param str name: external network name.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        platform = Platform(self.client)
        return platform.get_external_network(name)

    def add_external_network(self, network_name, ip_configuration):
        """Add the given external network to the gateway.

        :param str network_name: external network name.

        :param list ip_configuration: list of tuples that contain subnet in
            CIDR format and allocated ip address.
            Example [(10.10.10.1/24, Auto), (10.10.20.1/24, 10.10.20.3)]

        :return: object containing EntityType.TASK XML data representing the
            asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.reload()

        gateway = self.resource
        for inf in gateway.Configuration.GatewayInterfaces.GatewayInterface:
            if inf.Network.get('name') == network_name:
                raise AlreadyExistsException('External network ' +
                                             network_name +
                                             'already added to the gateway.')

        ext_nw = self._get_external_network(network_name)
        gw_interface = self._create_gateway_interface(ext_nw, 'uplink')

        # Add subnet participation
        ip_scopes = ext_nw.xpath(
            'vcloud:Configuration/vcloud:IpScopes/vcloud:IpScope',
            namespaces=NSMAP)
        for ip_scope in ip_scopes:
            subnet_participation_param = E.SubnetParticipation()
            subnet = None
            ext_nw_subnet = ip_scope.Gateway.text + '/' + \
                str(netmask_to_cidr_prefix_len(ip_scope.Gateway.text,
                                               ip_scope.Netmask.text))
            for sn in ip_configuration:
                if len(sn) != 2:
                    raise InvalidParameterException(
                        'IP Configuration should have both subnet and IP.')
                if sn[0] == ext_nw_subnet:
                    subnet = sn
                    break
            if subnet is None:
                continue

            ip_assigned = subnet[1].strip()
            # Configure Ip Settings
            subnet_participation_param.append(E.Gateway(ip_scope.Gateway.text))
            subnet_participation_param.append(E.Netmask(ip_scope.Netmask.text))

            if not ip_assigned and ip_assigned.lower() != 'auto':
                subnet_participation_param.append(E.IpAddress(ip_assigned))

            gw_interface.append(subnet_participation_param)

        gateway.Configuration.GatewayInterfaces.append(gw_interface)
        return self.client.put_linked_resource(
            self.resource, RelationType.GATEWAY_UPDATE_PROPERTIES,
            EntityType.EDGE_GATEWAY.value, gateway)

    def remove_external_network(self, network_name):
        """Remove the given external network to the gateway.

        :param str network_name: external network name.

        :return: object containing EntityType.TASK XML data representing the
            asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.reload()

        gateway = self.resource
        interfaces = gateway.Configuration.GatewayInterfaces
        for inf in interfaces.GatewayInterface:
            if inf.Network.get('name') == network_name:
                interfaces.remove(inf)
                break
        return self.client.put_linked_resource(
            self.resource, RelationType.GATEWAY_UPDATE_PROPERTIES,
            EntityType.EDGE_GATEWAY.value, gateway)

    def edit_gateway_name(self, newname=None):
        """It changes the old name of the gateway to the new name.

        :param String newname: new name of the gateway

        :return: object containing EntityType.TASK XML data
            representing the asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if newname is None:
            raise ValueError('Invalid input, name cannot be empty.')

        gateway = self.get_resource()
        gateway.set('name', newname)
        return self.client.put_linked_resource(self.resource,
                                               RelationType.EDIT,
                                               EntityType.EDGE_GATEWAY.value,
                                               gateway)

    def update_subnet_participation(self, subnets, subnet_participation):
        """It updates subnetparticipation of the gateway with subnets.

        :param subnets: dict of ipconfig settings for e.g.
                {192.168.1.1/24 :{'enable': True,
        'ip_address': '192.168.1.2'}}

        :param subnet_participation: object containing gateway's subnet
        """
        subnet_found = False
        for subnetpart in subnet_participation:
                subnet = subnets.get(subnetpart.Gateway.text + '/' + str(
                    netmask_to_cidr_prefix_len(subnetpart.Gateway.text,
                                               subnetpart.Netmask.text)))
                if subnet is not None:
                    subnet_found = True
                    if subnet.get('enable') is not None:
                        subnetpart.UseForDefaultRoute = E. \
                            UseForDefaultRoute(subnet.get('enable'))
                    if subnet.get('ip_address') is not None:
                        subnetpart.IpAddress = E.IpAddress(
                            subnet.get('ip_address'))

        if not subnet_found:
            raise ValueError('Subnet not found')

    def edit_config_ip_settings(self, ipconfig_settings=None):
        """It edits the config ip settings of gateway.

        User can only modify Subnet participation and config Ip address
        of gateway's external network.Expected subnet input should be in
        CIDR format.

        :param ipconfig_settings: dict of ipconfig settings for
        e.g: { extNetName:{192.168.1.1/24 :{'enable': True,
        'ip_address': '192.168.1.2'}},
        10.20.30.1/24: {'enable': True,
        'ip_address': '10.20.30.2'}}}

        :return: object containing EntityType.TASK XML data
                representing the asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        gateway = self.get_resource()
        externalnetwork_found = False
        for gatewayinf in \
                gateway.Configuration.GatewayInterfaces.GatewayInterface:
            if ipconfig_settings.get(gatewayinf.Name.text) is not None:
                externalnetwork_found = True
                subnets = ipconfig_settings.get(gatewayinf.Name.text)
                self.update_subnet_participation(subnets, gatewayinf.
                                                 SubnetParticipation)

        if not externalnetwork_found:
            raise ValueError('External network not found')

        return self.client.put_linked_resource(self.resource,
                                               RelationType.EDIT,
                                               EntityType.EDGE_GATEWAY.value,
                                               gateway)

    def __update_ip_ranges(self, subnet_participation, ip_range, new_ip_range):
        """Updates existing ip range element present in the sub static pool.

         It updates the existing ip range element present in the sub static
         pool of gateway.

        :param subnet_participation: SubnetParticipation object of the gateway

        :param ip_range: existing ip range present in the static pool
             allocation in the network. For example, [192.168.1.2-192.168.1.20]

        :param new_ip_range: new ip range to replace the existing ip range
             present in the static pool allocation in the network
        """
        old_start_end_range = ip_range.split('-')
        new_start_end_range = new_ip_range.split('-')
        for subnetpart in subnet_participation:
            for ip_range in subnetpart.IpRanges.IpRange:
                if old_start_end_range[0] == ip_range.StartAddress and \
                        old_start_end_range[1] == ip_range.EndAddress:
                    ip_range.StartAddress = E.StartAddress(
                        new_start_end_range[0])
                    ip_range.EndAddress = E.EndAddress(
                        new_start_end_range[1])
                    return
        raise EntityNotFoundException('IP Range \'%s\' not Found' % ip_range)

    def edit_sub_allocated_ip_pools(self, ext_network, ip_range,
                                    new_ip_change):
        """Edits existing ip range present in the sub allocate pool of gateway.

        :param ext_network: external network connected to the gateway

        :param ip_range: existing ip range present in the static pool
             allocation in the network. For example, [192.168.1.2-192.168.1.20]

        :param new_ip_change: new ip range to replace the existing ip range
             present in the static pool allocation in the network

        :return: object containing EntityType.TASK XML data
             representing the asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        gateway = self.get_resource()
        for gateway_inf in \
                gateway.Configuration.GatewayInterfaces.GatewayInterface:
            if gateway_inf.Name == ext_network:
                self.__update_ip_ranges(
                    gateway_inf.SubnetParticipation, ip_range,
                    new_ip_change)
                break

        return self.client.put_linked_resource(self.resource,
                                               RelationType.EDIT,
                                               EntityType.EDGE_GATEWAY.value,
                                               gateway)

    def get_sub_allocate_ip_ranges_element(self, subnet_participation):
        """Gets existing ip range present in the sub allocate pool of gateway.

        :param subnet_participation: SubnetParticipation object of the gateway.

        return: existing ip range.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        for subnetpart in subnet_participation:
            if hasattr(subnetpart, 'IpRanges'):
                return subnetpart.IpRanges
        return None

    def __add_ip_ranges_element(self, existing_ip_ranges, ip_ranges):
        """Adds to the existing ip range present in the sub allocate pool.

        :param existing_ip_ranges: existing ip range present in the sub
        allocate pool.

        :param ip_ranges: new ip range.
        """
        for range in ip_ranges:
            range_token = range.split('-')
            e_ip_range = E.IpRange()
            e_ip_range.append(E.StartAddress(range_token[0]))
            e_ip_range.append(E.EndAddress(range_token[1]))
            existing_ip_ranges.append(e_ip_range)

    def add_sub_allocated_ip_pools(self, ext_network, ip_ranges):
        """Adds new ip range present to the sub allocate pool of gateway.

        :param ext_network: external network connected to the gateway.

        :param ip_ranges: list of IP ranges used for static pool
            allocation in the network. For example, [192.168.1.2-192.168.1.49,
            192.168.1.100-192.168.1.149]

        :return: object containing EntityType.TASK XML data representing the
            asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        gateway = self.get_resource()
        for gateway_inf in \
                gateway.Configuration.GatewayInterfaces.GatewayInterface:
            if gateway_inf.Name == ext_network:
                subnet_participation = gateway_inf.SubnetParticipation
                existing_ip_ranges = self.get_sub_allocate_ip_ranges_element(
                    subnet_participation)
                if existing_ip_ranges is None:
                    existing_ip_ranges = E.IpRanges()
                    subnet_participation.IpAddress.addnext(existing_ip_ranges)
                self.__add_ip_ranges_element(existing_ip_ranges, ip_ranges)
                break

        return self.client.put_linked_resource(self.resource,
                                               RelationType.EDIT,
                                               EntityType.EDGE_GATEWAY.value,
                                               gateway)

    def __remove_ip_range_elements(self, existing_ip_ranges, ip_ranges):
        """Removes the given IP ranges from existing IP ranges.

        :param existing_ip_ranges: existing IP range present in the sub
                allocate pool.

        :param ip_ranges: IP ranges that needs to be removed.
        """
        for exist_range in existing_ip_ranges.IpRange:
            for remove_range in ip_ranges:
                address = remove_range.split('-')
                start_addr = address[0]
                end_addr = address[1]
                if start_addr == exist_range.StartAddress and \
                        end_addr == exist_range.EndAddress:
                    existing_ip_ranges.remove(exist_range)

    def remove_sub_allocated_ip_pools(self, ext_network, ip_ranges):
        """Removes the given IP ranges from the sub allocated pool..

        :param ext_network: external network connected to the gateway.

        :param ip_ranges: list of IP ranges that needs to be removed.
            For example, .... For example, [192.168.1.2-192.168.1.49,
            192.168.1.100-192.168.1.149]

        :return: object containing EntityType.TASK XML data representing the
            asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        gateway = self.get_resource()
        for gateway_inf in \
                gateway.Configuration.GatewayInterfaces.GatewayInterface:
            if gateway_inf.Name == ext_network:
                subnet_participation = gateway_inf.SubnetParticipation
                existing_ip_ranges = self.get_sub_allocate_ip_ranges_element(
                    subnet_participation)
                self.__remove_ip_range_elements(existing_ip_ranges, ip_ranges)
                if not hasattr(existing_ip_ranges, 'IpRange'):
                    subnet_participation.remove(existing_ip_ranges)
                break

        return self.client.put_linked_resource(self.resource,
                                               RelationType.EDIT,
                                               EntityType.EDGE_GATEWAY.value,
                                               gateway)
