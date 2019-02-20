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
from pyvcloud.vcd.client import create_element
from pyvcloud.vcd.client import E
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import find_link
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.exceptions import AlreadyExistsException
from pyvcloud.vcd.exceptions import EntityNotFoundException
from pyvcloud.vcd.exceptions import InvalidParameterException
from pyvcloud.vcd.network_url_constants import DHCP_URL_TEMPLATE
from pyvcloud.vcd.network_url_constants import FIREWALL_URL_TEMPLATE
from pyvcloud.vcd.network_url_constants import IPSEC_VPN_URL_TEMPLATE
from pyvcloud.vcd.network_url_constants import NAT_URL_TEMPLATE
from pyvcloud.vcd.network_url_constants import STATIC_ROUTE_URL_TEMPLATE
from pyvcloud.vcd.platform import Platform
from pyvcloud.vcd.utils import build_network_url_from_gateway_url
from pyvcloud.vcd.utils import get_admin_href
from pyvcloud.vcd.utils import netmask_to_cidr_prefix_len


class Gateway(object):
    __LEASE_TIME = '86400'
    __DEFAULT_ENCRYPTION_PROTOCOL = 'aes'
    __DEFAULT_AUTHENTICATION_MODE = 'psk'
    __DEFAULT_DH_GROUP = 'dh5'
    __DEFAULT_MTU = '1500'
    __DEFAULT_IP_SEC_ENABLE = True
    __DEFAULT_ENABLE_PFS = False
    __OBJECT_BROWSER_URL_PART = '/objectbrowser/edge'
    __FIREWALL_OBJECT_TYPE = '/firewall/{0}/{1}'
    __OBJECT_TYPE = '/firewall/{0}'
    __EDGES = '/edges'

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
        self.admin_resource = None

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

    def get_admin_resource(self):
        """Fetches the XML representation of the admin gateway from vCD.

        Will serve cached response if possible.

        :return: object containing EntityType.EDGE_GATEWAY XML data
        representing the gateway.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.admin_resource is None:
            self.reload_admin()
        return self.admin_resource

    def reload_admin(self):
        """Reloads the admin resource representation of the gateway.

        This method should be called in between two method invocations on the
        Admin Gateway object, if the former call changes the representation
        of the admin gateway in vCD.
        """
        self.admin_resource = self.client.get_resource(self.href_admin)
        if self.admin_resource is not None:
            self.href_admin = self.admin_resource.get('href')

    def convert_to_advanced(self):
        """Convert to advanced gateway.

        :return: object containing EntityType.TASK XML data representing the
            asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement

        """
        self.get_resource()

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
        self.get_admin_resource()
        gateway = self.admin_resource
        current_dr_status = gateway.Configuration.DistributedRoutingEnabled
        if enable == current_dr_status:
            return
        if enable:
            return self.client.post_linked_resource(
                gateway, RelationType.ENABLE_GATEWAY_DISTRIBUTED_ROUTING, None,
                None)
        if not enable:
            return self.client.post_linked_resource(
                gateway, RelationType.DISABLE_GATEWAY_DISTRIBUTED_ROUTING,
                None, None)

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
        self.get_resource()

        return self.client.post_linked_resource(
            self.resource, RelationType.GATEWAY_REDEPLOY, None, None)

    def sync_syslog_settings(self):
        """Sync syslog settings of the gateway.

        :return: object containing EntityType.TASK XML data representing the
            asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        self.get_resource()

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
                    gatewayips.append(subnetpart.Gateway.text + '/' + str(
                        netmask_to_cidr_prefix_len(subnetpart.Gateway.text,
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
        self.get_resource()

        gateway = self.resource
        for inf in gateway.Configuration.GatewayInterfaces.GatewayInterface:
            if inf.Network.get('name') == network_name:
                raise AlreadyExistsException('External network ' + network_name
                                             + 'already added to the gateway.')

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
        self.get_resource()

        gateway = self.resource
        interfaces = gateway.Configuration.GatewayInterfaces
        for inf in interfaces.GatewayInterface:
            if inf.Network.get('name') == network_name:
                interfaces.remove(inf)
                break
        return self.client.put_linked_resource(
            self.resource, RelationType.GATEWAY_UPDATE_PROPERTIES,
            EntityType.EDGE_GATEWAY.value, gateway)

    def edit_gateway(self, newname=None, desc=None, ha=None):
        """It changes the old name of the gateway to the new name.

        :param str newname: new name of the gateway
        :param str desc: description of the gateway
        :param bool ha: HA of the gateway

        :return: object containing EntityType.TASK XML data
            representing the asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: ValueError: if the values are not provided.
        """
        if newname is None and desc is None and ha is None:
            raise ValueError('Invalid input, please provide at least one '
                             'parameter')

        gateway = self.get_resource()
        if newname:
            gateway.set('name', newname)
        if desc:
            if hasattr(gateway, 'Description'):
                gateway.Description = E.Description(desc)
            else:
                gateway.insert(0, E.Description(desc))
        if ha:
            gateway.Configuration.HaEnabled = E.HaEnabled(ha)

        return self.client.put_linked_resource(
            self.resource, RelationType.EDIT, EntityType.EDGE_GATEWAY.value,
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
                self.update_subnet_participation(
                    subnets, gatewayinf.SubnetParticipation)

        if not externalnetwork_found:
            raise ValueError('External network not found')

        return self.client.put_linked_resource(
            self.resource, RelationType.EDIT, EntityType.EDGE_GATEWAY.value,
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
                    ip_range.EndAddress = E.EndAddress(new_start_end_range[1])
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
                self.__update_ip_ranges(gateway_inf.SubnetParticipation,
                                        ip_range, new_ip_change)
                break

        return self.client.put_linked_resource(
            self.resource, RelationType.EDIT, EntityType.EDGE_GATEWAY.value,
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

        return self.client.put_linked_resource(
            self.resource, RelationType.EDIT, EntityType.EDGE_GATEWAY.value,
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
            For example, [192.168.1.2-192.168.1.49,
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

        return self.client.put_linked_resource(
            self.resource, RelationType.EDIT, EntityType.EDGE_GATEWAY.value,
            gateway)

    def edit_rate_limits(self, rate_limit_configs):
        """Edits existing rate limit of gateway.

        :param rate_limit_configs: dict of external network vs rate limit
        for e.g.
        { extNework1:['101.0', '101.0'],
          extNework2:['101.0', '101.0']
        }

        :return: object containing EntityType.TASK XML data
             representing the asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        gateway = self.get_resource()
        for gateway_inf in \
                gateway.Configuration.GatewayInterfaces.GatewayInterface:
            ext_name = gateway_inf.Name.text
            if rate_limit_configs.get(ext_name) is not None:
                rate_limit_range = rate_limit_configs.get(ext_name)
                gateway_inf.InRateLimit = E.InRateLimit(rate_limit_range[0])
                gateway_inf.OutRateLimit = E.OutRateLimit(rate_limit_range[1])

        return self.client.put_linked_resource(
            self.resource, RelationType.EDIT, EntityType.EDGE_GATEWAY.value,
            gateway)

    def set_tenant_syslog_server_ip(self, ip):
        """Set syslog server ip of the gateway.

        This operation can be performed by System/Org Administrators.

        :param: str ip: IP to be added as Syslog server IP
        :return: object containing EntityType.TASK XML data
             representing the asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        gateway = self.get_resource()
        link = find_link(gateway,
                         RelationType.GATEWAY_SYS_SERVER_SETTING_IP,
                         EntityType.EDGE_GATEWAY_SYS_LOG_SERVER_IP.value)
        syslog_server_settings = gateway.Configuration.SyslogServerSettings

        if hasattr(syslog_server_settings, 'TenantSyslogServerSettings'):
            syslog_server_settings.TenantSyslogServerSettings.append(
                E.SyslogServerIp(ip))

        return self.client.post_resource(link.href, syslog_server_settings,
                                         EntityType
                                         .EDGE_GATEWAY_SYS_LOG_SERVER_IP.value)

    def list_syslog_server_ip(self):
        """List syslog server ip of the gateway.

        This operation can be performed by System/Org Administrators.

        :return: a dictionary that maps tenant syslog server to ip
            address. Ex: {'Tenant Syslog server:': '1.1.1.1'}

        :rtype: dict
        """
        gateway = self.get_resource()
        out = {}
        syslogserver_settings = gateway.Configuration.SyslogServerSettings.\
            TenantSyslogServerSettings
        if hasattr(syslogserver_settings, 'SyslogServerIp'):
            out["Tenant Syslog server"] = syslogserver_settings.SyslogServerIp
        else:
            raise EntityNotFoundException('TenantSyslogServer Ip in gateway' +
                                          self.name + 'is not set.')
        return out

    def add_firewall_rule(self,
                          name,
                          action='accept',
                          type='User',
                          enabled=True,
                          logging_enabled=False):
        """Add firewall rule in the gateway.

        param name str: name of firewall rule
        param action str: action. Possible values accept/deny.
        param type str: firewall rule type. Default: User
        param enable bool: enable
        param logging_enabled bool: logging enabled

        """
        firewall_rule_href = self._build_firewall_rule_href()
        firewall_rules_resource = self.get_firewall_rules()
        firewall_rules_tag = firewall_rules_resource.firewallRules
        firewall_rule = E.firewallRule()
        firewall_rule.append(E.name(name))
        firewall_rule.append(E.ruleType(type))
        firewall_rule.append(E.enabled(enabled))
        firewall_rule.append(E.loggingEnabled(logging_enabled))
        firewall_rule.append(E.action(action))

        firewall_rules_tag.append(firewall_rule)
        self.client.put_resource(firewall_rule_href, firewall_rules_resource,
                                 EntityType.DEFAULT_CONTENT_TYPE.value)

    def get_firewall_rules(self):
        """Get firewall Rules from vCD.

        Form a Firewall Rules using gateway href and fetches from vCD.

        return: FirewallRule Object
        """
        firewall_rule_href = self._build_firewall_rule_href()
        return self.client.get_resource(firewall_rule_href)

    def _build_firewall_rule_href(self):
        network_url = build_network_url_from_gateway_url(self.href)
        return network_url + FIREWALL_URL_TEMPLATE

    def _build_dhcp_href(self):
        network_url = build_network_url_from_gateway_url(self.href)
        return network_url + DHCP_URL_TEMPLATE

    def get_dhcp(self):
        """Get DHCP from vCD.

        Form a DHCP using gateway href.

        return: DHCP Object
        """
        dhcp_pool_href = self._build_dhcp_href()
        return self.client.get_resource(dhcp_pool_href)

    def list_rate_limits(self):
        """Lists rate limit of gateway.

        :return: list of dictionary that has gateway's rate limit settings
        for e.g.
        [{ external_network:extNework2,
          in_rate_limit:101.0
          out_rate_limit:101.0
        }]

        :rtype: list
        """
        gateway = self.get_resource()
        out_list = []
        for gateway_inf in \
                gateway.Configuration.GatewayInterfaces.GatewayInterface:
            rate_limit_setting = dict()
            if hasattr(gateway_inf, 'InRateLimit') and \
                    hasattr(gateway_inf, 'OutRateLimit'):
                rate_limit_setting['external_network'] = gateway_inf.Name.text
                rate_limit_setting['in_rate_limit'] = \
                    gateway_inf.InRateLimit.text
                rate_limit_setting['out_rate_limit'] = \
                    gateway_inf.OutRateLimit.text

            out_list.append(rate_limit_setting)

        return out_list

    def disable_rate_limits(self, ext_Networks):
        """Disable rate limit of gateway for provided external networks.

        :param ext_Networks: List of external network
        for e.g.
        [extNework1, extNework2]

        :return: object containing EntityType.TASK XML data
             representing the asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        gateway = self.get_resource()
        for gateway_inf in \
                gateway.Configuration.GatewayInterfaces.GatewayInterface:
            ext_name = gateway_inf.Name.text
            if ext_name in ext_Networks:
                if hasattr(gateway_inf, 'InRateLimit') and \
                        hasattr(gateway_inf, 'OutRateLimit'):
                    gateway_inf.ApplyRateLimit = E.ApplyRateLimit('false')
                    gateway_inf.remove(gateway_inf.InRateLimit)
                    gateway_inf.remove(gateway_inf.OutRateLimit)

        return self.client.put_linked_resource(
            self.resource, RelationType.EDIT, EntityType.EDGE_GATEWAY.value,
            gateway)

    def __update_dns_relay(self, configuration, enable_dns_relay=None):
        """Updates DNS Relay of a gateway.

        :param configuration: gateway configuration
        :param bool enable_dns_relay: flag to enable/disable DNS Relay
        """
        if enable_dns_relay is not None and \
                hasattr(configuration, 'UseDefaultRouteForDnsRelay'):
            configuration.UseDefaultRouteForDnsRelay = \
                E.UseDefaultRouteForDnsRelay(enable_dns_relay)

    def __update_gateway_default_route(self,
                                       gateway_inf,
                                       enable_default_gateway=None):
        """Updates default route of gateway interface.

        :param gateway_inf: gateway interface.
        :param bool enable_default_gateway: flag to enable/disable default
            gateway
        """
        if enable_default_gateway is not None and \
                hasattr(gateway_inf, 'UseForDefaultRoute'):
            gateway_inf.UseForDefaultRoute = \
                E.UseForDefaultRoute(enable_default_gateway)

    def __update_subnet_participation_default_route(
            self, subnet, gateway_ip, enable_default_gateway=None):
        """Updates default route of subnet participation of gateway.

        :param subnet: subnet participation of gateway.
        :param bool enable_default_gateway: flag to enable/disable default
            gateway
        """
        if enable_default_gateway is not None and \
                hasattr(subnet, 'UseForDefaultRoute') and \
                subnet.Gateway == gateway_ip:
            subnet.UseForDefaultRoute = \
                E.UseForDefaultRoute(enable_default_gateway)

    def configure_default_gateway(self, ext_network, ip,
                                  enable_default_gateway):
        """Configures gateway for provided external networks and gateway IP.

        :param ext_network: External network connected to gateway
        :param ip: default ip of the gateway
        :param bool enable_default_gateway: flag to enable/disable default
            gateway

        :return: object containing EntityType.TASK XML data
             representing the asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        gateway = self.get_resource()

        for gateway_inf in \
                gateway.Configuration.GatewayInterfaces.GatewayInterface:
            ext_name = gateway_inf.Name.text
            if ext_name == ext_network:
                subnet_participation = gateway_inf.SubnetParticipation
                self.__update_gateway_default_route(gateway_inf,
                                                    enable_default_gateway)
                self.__update_subnet_participation_default_route(
                    subnet_participation, ip, enable_default_gateway)

        return self.client.put_linked_resource(
            self.resource, RelationType.EDIT, EntityType.EDGE_GATEWAY.value,
            gateway)

    def configure_dns_default_gateway(self, enable_dns_relay):
        """Enables/disables the dns relay of the default gateway.

        :param bool enable_dns_relay: flag to enable/disable DNS Relay

        :return: object containing EntityType.TASK XML data
             representing the asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        gateway = self.get_resource()
        self.__update_dns_relay(gateway.Configuration, enable_dns_relay)

        return self.client.put_linked_resource(
            self.resource, RelationType.EDIT, EntityType.EDGE_GATEWAY.value,
            gateway)

    def list_configure_default_gateway(self):
        """Lists the configured default gateway.

        :return: list of dictionary that has external network and default
            gateway ip, for e.g.
            [{ external_network:extNework1,
               gateway_ip:2.2.3.1
            }]

        :rtype: list
        """
        gateway = self.get_resource()
        out_list = []
        for gateway_inf in \
                gateway.Configuration.GatewayInterfaces.GatewayInterface:
            gateway_config = dict()
            if gateway_inf.UseForDefaultRoute:
                gateway_config['external_network'] = gateway_inf.Name.text
                for subnet_part in gateway_inf.SubnetParticipation:
                    if subnet_part.UseForDefaultRoute:
                        gateway_config['gateway_ip'] = \
                            subnet_part.Gateway.text
                        out_list.append(gateway_config)
        return out_list

    def add_dhcp_pool(self,
                      ip_range,
                      auto_config_dns=False,
                      default_gateway=None,
                      domain_name=None,
                      lease_never_expires=False,
                      lease_time=__LEASE_TIME,
                      subnet_mask=None,
                      primary_server=None,
                      secondary_server=None):
        """Add DHCP pool in the gateway.

        param str ip_range: IP range for the DHCP pools
        param bool auto_config_dns : auto configuration of DNS Default : false
        param str default_gateway: default gateway ip
        param str domain_name: domain name
        param bool lease_never_expires: lease expires Default : false
        param str lease_time: time for the expiration of lease Default : 86400
        param str subnet_mask: subnet mask of the DHCP pool
        param str primary_server: IP of the primary server
        param str secondary_server: IP of the secondary server

        """
        dhcp_pool_href = self._build_dhcp_href()
        dhcp_resource = self.get_dhcp()

        ip_pool_tag = create_element("ipPool")
        ip_pool_tag.append(create_element("autoConfigureDNS", auto_config_dns))
        if default_gateway is not None:
            ip_pool_tag.appendcreate_element("defaultGateway", default_gateway)
        if domain_name is not None:
            ip_pool_tag.append(create_element("domainName", domain_name))
        if primary_server is not None:
            ip_pool_tag.append(
                create_element("primaryNameServer", primary_server))
        if secondary_server is not None:
            ip_pool_tag.append(
                create_element("secondaryNameServer", secondary_server))

        if lease_never_expires:
            ip_pool_tag.append(create_element("leaseTime", "infinite"))
        else:
            ip_pool_tag.append(create_element("leaseTime", lease_time))

        if subnet_mask is not None:
            ip_pool_tag.append(create_element("subnetMask", subnet_mask))

        ip_pool_tag.append(create_element("ipRange", ip_range))
        dhcp_resource.ipPools.append(ip_pool_tag)

        self.client.put_resource(dhcp_pool_href, dhcp_resource,
                                 EntityType.DEFAULT_CONTENT_TYPE.value)

    def add_nat_rule(self,
                     action,
                     original_address,
                     translated_address,
                     description=None,
                     protocol='any',
                     original_port='any',
                     translated_port='any',
                     type='User',
                     icmp_type='any',
                     logging_enabled=False,
                     enabled=True,
                     vnic=0):
        """Add nat rule in the gateway.

        param action str: action having values snat/dnat
        param original_address str: original IP address
        param translated_address str: translated IP address
        param description str: nat rule description
        param protocol str: protocol such as tcp/udp/icmp
        param original_port: port no. such as FTP(21)
        param translated_port: port no. such as HTTP(80)
        param type str: nat rule type. Default: User
        param icmp_type str: icmp type such as "Echo-request"
        param logging_enabled bool: logging enabled
        param enable bool: enable nat rule
        param int vnic: interface of gateway

        """
        nat_rule_href = self._build_nat_rule_href()
        nat_rules_resource = self.get_nat_rules()
        nat_rules_tag = nat_rules_resource.natRules
        nat_rule = E.natRule()
        nat_rule.append(E.ruleType(type))
        nat_rule.append(E.action(action))
        nat_rule.append(E.originalAddress(original_address))
        nat_rule.append(E.translatedAddress(translated_address))
        nat_rule.append(E.loggingEnabled(logging_enabled))
        nat_rule.append(E.enabled(enabled))
        nat_rule.append(E.description(description))
        # This field is optional
        nat_rule.append(E.vnic(vnic))

        # DNAT rule requries additonal parameters
        if action == 'dnat' and protocol != 'icmp':
            nat_rule.append(E.protocol(protocol))
            nat_rule.append(E.originalPort(original_port))
            nat_rule.append(E.translatedPort(translated_port))

        if action == 'dnat' and protocol == 'icmp':
            nat_rule.append(E.translatedPort(translated_port))
            nat_rule.append(E.protocol(protocol))
            nat_rule.append(E.icmpType(icmp_type))

        nat_rules_tag.append(nat_rule)
        self.client.put_resource(nat_rule_href, nat_rules_resource,
                                 EntityType.DEFAULT_CONTENT_TYPE.value)

    def get_nat_rules(self):
        """Get Nat Rules from vCD.

        Form a Nat Rules using gateway href and fetches from vCD.

        return: NatRule Object
        """
        nat_rule_href = self._build_nat_rule_href()
        return self.client.get_resource(nat_rule_href)

    def _build_nat_rule_href(self):
        network_url = build_network_url_from_gateway_url(self.href)
        return network_url + NAT_URL_TEMPLATE

    def list_nat_rules(self):
        """List all nat rules on a gateway.

        :return: list of all nat rules on a gateway.
        e.g.
        [{'ID': 196609, 'Action': 'snat', 'Enabled': True}]
        """
        out_list = []
        nat_rules_resource = self.get_nat_rules()
        if (hasattr(nat_rules_resource.natRules, 'natRule')):
            for nat_rule in nat_rules_resource.natRules.natRule:
                nat_rule_info = {}
                nat_rule_info['ID'] = nat_rule.ruleId
                nat_rule_info['Action'] = nat_rule.action
                nat_rule_info['Enabled'] = nat_rule.enabled
                out_list.append(nat_rule_info)
        return out_list

    def list_dhcp_pools(self):
        """List all DHCP pools on a gateway.

        :return: list of all DHCP pools on a gateway.
        e.g.
        [{'ID': pool-1, 'IP_range': '30.20.10.11-30.20.10.15',
        'Auto_configure_dns': True}]
        """
        out_list = []
        dhcp_resource = self.get_dhcp()
        if hasattr(dhcp_resource.ipPools, 'ipPool'):
            for ip_pool in dhcp_resource.ipPools.ipPool:
                pool_info = dict()
                pool_info['ID'] = ip_pool.poolId
                pool_info['IP_Range'] = ip_pool.ipRange
                pool_info['Auto_Configure_Dns'] = ip_pool.autoConfigureDNS
                out_list.append(pool_info)
        return out_list

    def get_firewall_rules_list(self):
        """List all firewall rules of a gateway.

        :return: list of all firewall rules of a gateway.
        e.g.
        [{'ID': 12344, 'name': 'firewall','ruleType': 'internal_high'}]
        """
        firewall_rules = self.get_firewall_rules()
        firewall_rule_list = []
        if hasattr(firewall_rules.firewallRules, 'firewallRule'):
            for firewall_rule in firewall_rules.firewallRules.firewallRule:
                firewall_rule_list.append(
                    dict(
                        ID=firewall_rule['id'],
                        name=firewall_rule['name'],
                        ruleType=firewall_rule['ruleType']))
        return firewall_rule_list

    def add_static_route(self,
                         network,
                         next_hop,
                         mtu=1500,
                         description=None,
                         type='User',
                         vnic=0):
        """Add Static Route in the gateway.

        param network str: vApp/Org vDC Network in CIDR format
        e.g. 192.169.1.0/24
        param next_hop str: IP address of next hop
        param mtu int: Maximum Transmission Units (MTU) e.g 1500 MTU
        param description str: static route description
        param type str: static route type. Default: User
        param vnic int: interface of gateway

        """
        static_route_href = self._build_static_routes_href()
        static_routes_resource = self.get_static_routes()
        static_route_tag = static_routes_resource.staticRoutes
        static_route = E.route()
        static_route.append(E.network(network))
        static_route.append(E.nextHop(next_hop))
        static_route.append(E.mtu(mtu))
        static_route.append(E.type(type))
        static_route.append(E.description(description))
        static_route.append(E.vnic(vnic))
        static_route_tag.append(static_route)
        self.client.put_resource(static_route_href, static_routes_resource,
                                 EntityType.DEFAULT_CONTENT_TYPE.value)

    def get_static_routes(self):
        """Get Static Routes from vCD.

        Form Static Routes using gateway href and fetches from vCD.

        return: staticRoutes Object
        """
        static_route_href = self._build_static_routes_href()
        return self.client.get_resource(static_route_href)

    def _build_static_routes_href(self):
        network_url = build_network_url_from_gateway_url(self.href)
        return network_url + STATIC_ROUTE_URL_TEMPLATE

    def list_static_routes(self):
        """List all Static Routes on a gateway.

        :return: list of all static routes on a gateway.
        e.g.
        [{'Network': '192.169.1.0/24', 'Next Hop': '2.2.3.80', 'MTU': 1500}]
        """
        out_list = []
        static_routes_resource = self.get_static_routes()
        if hasattr(static_routes_resource.staticRoutes, 'route'):
            for static_route in static_routes_resource.staticRoutes.route:
                static_route_info = {}
                static_route_info['Network'] = static_route.network
                static_route_info['Next Hop'] = static_route.nextHop
                static_route_info['MTU'] = static_route.mtu
                out_list.append(static_route_info)
        return out_list

    def add_ipsec_vpn(self,
                      name,
                      peer_id,
                      peer_ip_address,
                      local_id,
                      local_ip_address,
                      local_subnet,
                      peer_subnet,
                      shared_secret_encrypted,
                      encryption_protocol=__DEFAULT_ENCRYPTION_PROTOCOL,
                      authentication_mode=__DEFAULT_AUTHENTICATION_MODE,
                      dh_group=__DEFAULT_DH_GROUP,
                      description=None,
                      mtu=__DEFAULT_MTU,
                      is_enabled=__DEFAULT_IP_SEC_ENABLE,
                      enable_pfs=__DEFAULT_ENABLE_PFS):
        """Add IPsec VPN in the gateway.

        param str name: name of IPSec VPN
        param str description: description of IPSec VPN
        param str peer_id: peer id
        param str peer_ip_address: peer IP address
        param str local_id: local id
        param str local_ip_address: local IP address
        param str local_subnet: local subnet in CIDR format
        param str peer_subnet: peer subnet in CIDR format
        param str shared_secret_encrypted: shared secret encrypted
        param str encryption_protocol: encryption protocol
        param str authentication_mode: authentication mode
        param str dh_group: dh group
        param str mtu: MTU
        param bool is_enabled: enabled status Default : false
        param bool enable_pfs: enable pfs status Default : false
        :return: Ipsec Vpn object

        :rtype: lxml.objectify.ObjectifiedElement
        """
        ipsec_vpn_href = self._build_ipsec_vpn_href()
        ipsec_vpn_resource = self.get_ipsec_vpn()
        vpn_sites = ipsec_vpn_resource.sites
        site = E.site()
        site.append(E.enabled(is_enabled))
        site.append(E.name(name))
        site.append(E.description(description))
        site.append(E.localId(local_id))
        site.append(E.localIp(local_ip_address))
        site.append(E.peerId(peer_id))
        site.append(E.peerIp(peer_ip_address))
        site.append(E.encryptionAlgorithm(encryption_protocol))
        site.append(E.mtu(mtu))
        site.append(E.enablePfs(enable_pfs))
        local_subnets = E.localSubnets()
        if ',' in local_subnet:
            subnet_list = local_subnet.split(",")
            for subnet in subnet_list:
                local_subnets.append(E.subnet(subnet))
        else:
            local_subnets.append(E.subnet(local_subnet))
        peer_subnets = E.peerSubnets()
        if ',' in peer_subnet:
            subnet_list = peer_subnet.split(",")
            for subnet in subnet_list:
                peer_subnets.append(E.subnet(subnet))
        else:
            peer_subnets.append(E.subnet(peer_subnet))
        site.append(local_subnets)
        site.append(peer_subnets)
        site.append(E.psk(shared_secret_encrypted))
        site.append(E.authenticationMode(authentication_mode))
        site.append(E.dhGroup(dh_group))
        vpn_sites.append(site)

        self.client.put_resource(ipsec_vpn_href, ipsec_vpn_resource,
                                 EntityType.DEFAULT_CONTENT_TYPE.value)

    def _build_ipsec_vpn_href(self):
        network_url = build_network_url_from_gateway_url(self.href)
        return network_url + IPSEC_VPN_URL_TEMPLATE

    def get_ipsec_vpn(self):
        """Get IPSec VPN from vCD.

        Form a IPSec VPN using gateway href.
        :rtype: lxml.objectify.ObjectifiedElement
        """
        ipsec_vpn_href = self._build_ipsec_vpn_href()
        return self.client.get_resource(ipsec_vpn_href)

    def enable_activation_status_ipsec_vpn(self, is_active):
        """Enables activation status of IPsec VPN.

        :param bool is_active: flag to enable/disable activation status
        """
        ipsec_vpn = self.get_ipsec_vpn()
        ipsec_vpn.enabled = is_active
        self.client.put_resource(self._build_ipsec_vpn_href(),
                                 ipsec_vpn,
                                 EntityType.DEFAULT_CONTENT_TYPE.value)

    def info_activation_status_ipsec_vpn(self):
        """Info activation status.

        :return: dict activation status dict
        """
        ipsec_vpn_activation_status = {}
        ipsec_vpn = self.get_ipsec_vpn()
        ipsec_vpn_activation_status["Activation Status"] = \
            ipsec_vpn.enabled.text
        return ipsec_vpn_activation_status

    def change_shared_key_ipsec_vpn(self, shared_key):
        """Changes shared key.

        :param str shared_key: shared key.
        """
        ipsec_vpn = self.get_ipsec_vpn()
        ip_sec_global = ipsec_vpn.xpath('global', namespaces=NSMAP)
        ip_sec_global[0].psk = shared_key

        self.client.put_resource(self._build_ipsec_vpn_href(),
                                 ipsec_vpn,
                                 EntityType.DEFAULT_CONTENT_TYPE.value)

    def enable_logging_ipsec_vpn(self, is_enable):
        """Enables logging for IPsec VPN.

        :param bool is_enable: flag to enable/disable logging.
        """
        ipsec_vpn = self.get_ipsec_vpn()
        ipsec_vpn.logging.enable = is_enable
        self.client.put_resource(self._build_ipsec_vpn_href(),
                                 ipsec_vpn,
                                 EntityType.DEFAULT_CONTENT_TYPE.value)

    def set_log_level_ipsec_vpn(self, log_level):
        """Set log level for Ipsec VPN.

        :param str log_level: log level
        """
        log_level_set = set(
            ["emergency", "alert", "critical", "error", "warning",
             "notice", "info", "debug"])
        if log_level not in log_level_set:
            raise EntityNotFoundException('No associated log level found.')

        ipsec_vpn = self.get_ipsec_vpn()
        ipsec_vpn.logging.logLevel = log_level
        self.client.put_resource(self._build_ipsec_vpn_href(),
                                 ipsec_vpn,
                                 EntityType.DEFAULT_CONTENT_TYPE.value)

    def info_logging_settings_ipsec_vpn(self):
        """Provide info for logging settings.

        :return: dict: dict of info of logging settings
        """
        ipsec_logging_settings = {}
        ipsec_vpn = self.get_ipsec_vpn()
        ipsec_logging_settings["Enable"] = \
            ipsec_vpn.logging.enable.text
        ipsec_logging_settings["Log Level"] = \
            ipsec_vpn.logging.logLevel

        return ipsec_logging_settings

    def list_ipsec_vpn(self):
        """List IPsec VPN of a gateway.

        :return: list of all ipsec vpn.
        """
        out_list = []
        ipsec_vpn = self.get_ipsec_vpn()
        vpn_sites = ipsec_vpn.sites
        if hasattr(vpn_sites, "site"):
            for site in vpn_sites.site:
                ipsec_vpn_info = {}
                ipsec_vpn_info["Name"] = site.name
                ipsec_vpn_info["local_ip"] = site.localIp
                ipsec_vpn_info["peer_ip"] = site.peerIp
                out_list.append(ipsec_vpn_info)
        return out_list

    def list_firewall_object_types(self, type):
        """List firewall object types for editing of rule.

        :param type: Operation Type. It can source/destination

        :return: list of dict

        :rtype: list
        """
        object_type_url = self.__build_object_type_url(type)
        object = self.client.get_resource(object_type_url)
        response = []
        for object_result in object.objectBrowserResult:
            result = {}
            result['name'] = object_result.name
            result['object_type'] = object_result.type.text.lower()
            result['link'] = object_result.link
            response.append(result)
        return response

    def __build_object_type_url(self, type):
        """Build object browser URL.

        :param type: Operation Type. It can source/destination

        :return: object browser url of object_type. e.g.,
        https://{0}/network/objectbrowser/edge/{1}/firewall/source
        :rtype: str
        """
        _network_url = build_network_url_from_gateway_url(self.href)
        object_browser_url = \
            _network_url.replace(Gateway.__EDGES,
                                 Gateway.__OBJECT_BROWSER_URL_PART) + \
            Gateway.__OBJECT_TYPE
        object_browser_url = object_browser_url.format(type)
        return object_browser_url

    def __build_object_browser_url(self, type, object_type):
        """Build object browser URL.

        :param type: Operation Type. It can source/destination
        :param object_type: Possible values:
        gatewayinterface/virtualmachine/network/ipset/securitygroup
        :return: object browser url of object_type. e.g.,
        https://{0}/network/objectbrowser/edge/{1}/firewall/source/
        gatewayinterface
        :return: URL of object
        :rtype: str
        """
        _network_url = build_network_url_from_gateway_url(self.href)
        object_browser_url = \
            _network_url.replace(Gateway.__EDGES,
                                 Gateway.__OBJECT_BROWSER_URL_PART) + \
            Gateway.__FIREWALL_OBJECT_TYPE
        object_browser_url = object_browser_url.format(type, object_type)
        return object_browser_url

    def __build_object_browser_response(self, type, object_type):
        """Build object response and mapping into list of dict.

        param type: type. It can be source/destination.
        param object_type: object type. It can be
        gatewayinterface/virtualmachine/network/ipset/securitygroup

        :return: list of dict
        :rtype: list
        """
        object_url = self.__build_object_browser_url(type, object_type)
        object = self.client.get_resource(object_url)
        response = []
        if int(object.get('total')) <= 0:
            return response
        for object_result in object.objectBrowserResult:
            result = {}
            result['type'] = object_result.type
            result['name'] = object_result.name
            obj_browser_props_list = []
            if not (hasattr(object_result, 'requiredProperties') and
                    hasattr(object_result.requiredProperties,
                            'objectBrowserProperty')):
                continue

            for obj_browser_prop in \
                    object_result.requiredProperties.objectBrowserProperty:
                obj_browser_props = {}
                obj_browser_props['name'] = obj_browser_prop.get('name')
                obj_browser_props['value'] = obj_browser_prop.get('value')

                obj_browser_props_list.append(obj_browser_props)

            result['prop'] = obj_browser_props_list
            response.append(result)

        return response

    def list_firewall_objects(self, type, object_type):
        """List firewall's objects for editing firewall rule.

        :param type: Operation Type. It can source/destination
        :param object_type: Possible values:
        gatewayinterface/virtualmachine/network/ipset/securitygroup
        :return: list of dict
        :rtype: list
        """
        return self.__build_object_browser_response(type, object_type)

    def reorder_nat_rule(self, rule_id, position):
        """Reorder the nat rule position on gateway.

        param rule_id str: id of snat/dnat rule
        param position int: postion where nat rule will be inserted
        """
        insert_nat_rule = None
        nat_rule_href = self._build_nat_rule_href()
        nat_rules_resource = self.get_nat_rules()
        if (hasattr(nat_rules_resource.natRules, 'natRule')):
            for nat_rule in nat_rules_resource.natRules.natRule:
                if int(nat_rule.ruleId) == int(rule_id):
                    insert_nat_rule = nat_rule
                    # remove the nat rule from existing position
                    nat_rules_resource.natRules.remove(nat_rule)
                    break

        # insert the nat rule at new position
        nat_rules_resource.natRules.insert(position,
                                           insert_nat_rule)
        self.client.put_resource(nat_rule_href, nat_rules_resource,
                                 EntityType.DEFAULT_CONTENT_TYPE.value)

    def add_dhcp_binding(self,
                         mac,
                         host_name,
                         ip_address,
                         auto_config_dns=False,
                         primary_server=None,
                         secondary_server=None,
                         default_gateway=None,
                         domain_name=None,
                         lease_never_expires=False,
                         lease_time=__LEASE_TIME,
                         subnet_mask=None):
        """Add DHCP binding in the gateway.

        param str mac: MAC address for the DHCP binding
        param str host_name: host name for the DHCP binding
        param str ip_address: IP address for the DHCP binding
        param bool auto_config_dns : auto configuration of DNS Default : false
        param str primary_server: IP of the primary server
        param str secondary_server: IP of the secondary server
        param str default_gateway: default gateway ip
        param str domain_name: domain name
        param bool lease_never_expires: lease expires Default : false
        param str lease_time: time for the expiration of lease Default : 86400
        param str subnet_mask: subnet mask of the DHCP binding

        """
        dhcp_href = self._build_dhcp_href()
        dhcp_resource = self.get_dhcp()

        static_binding = create_element("staticBinding")
        static_binding.append(create_element("hostname", host_name))
        static_binding.append(create_element("macAddress", mac))
        static_binding.append(create_element("ipAddress", ip_address))
        auto_config_dns_element = create_element("autoConfigureDNS",
                                                 auto_config_dns)
        static_binding.append(auto_config_dns_element)
        if auto_config_dns:
            static_binding.append(create_element("primaryNameServer", "Auto"))
            static_binding.append(
                create_element("secondaryNameServer", "Auto"))
        else:
            if primary_server:
                static_binding.append(
                    create_element("primaryNameServer", primary_server))
            if secondary_server:
                static_binding.append(
                    create_element("secondaryNameServer", secondary_server))

        if default_gateway:
            static_binding.appendcreate_element("defaultGateway",
                                                default_gateway)
        if domain_name:
            static_binding.append(create_element("domainName", domain_name))

        if lease_never_expires:
            static_binding.append(create_element("leaseTime", "infinite"))
        else:
            static_binding.append(create_element("leaseTime", lease_time))

        if subnet_mask:
            static_binding.append(create_element("subnetMask", subnet_mask))

        dhcp_resource.staticBindings.append(static_binding)

        self.client.put_resource(dhcp_href, dhcp_resource,
                                 EntityType.DEFAULT_CONTENT_TYPE.value)

    def list_dhcp_binding(self):
        """List all DHCP bindings on a gateway.

        :return: list of all DHCP bindings on a gateway.
        e.g.
        [{'ID': binding-1, 'MAC_Address': '00:14:22:01:23:44',
          'IP_Address': '10.20.30.40'}]
        """
        out_list = []
        dhcp_resource = self.get_dhcp()
        if hasattr(dhcp_resource.staticBindings, 'staticBinding'):
            for static_binding in dhcp_resource.staticBindings.staticBinding:
                pool_info = dict()
                pool_info['ID'] = static_binding.bindingId
                pool_info['MAC_Address'] = static_binding.macAddress
                pool_info['IP_Address'] = static_binding.ipAddress
                out_list.append(pool_info)
        return out_list
