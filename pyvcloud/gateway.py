# VMware vCloud Python SDK
# Copyright (c) 2014 VMware, Inc. All Rights Reserved.
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

# coding: utf-8

import requests
from schema.vcd.v1_5.schemas.vcloud import taskType
from schema.vcd.v1_5.schemas.vcloud.networkType import NatRuleType, GatewayNatRuleType, ReferenceType, NatServiceType, FirewallRuleType, ProtocolsType, DhcpPoolServiceType, GatewayIpsecVpnServiceType, GatewayIpsecVpnEndpointType, GatewayIpsecVpnTunnelType, IpsecVpnSubnetType, IpsecVpnThirdPartyPeerType, DhcpServiceType, GatewayDhcpServiceType
from iptools import IpRange
from helper import CommonUtils
from xml.etree import ElementTree as ET
from netaddr import *
from pyvcloud import _get_logger, Http

DEFAULT_LEASE = 3600
MAX_LEASE = 7200


class Gateway(object):

    def __init__(self, gateway, headers, verify, busy, log=False):
        self.me = gateway
        self.headers = headers
        self.verify = verify
        self.response = None
        self.logger = _get_logger() if log else None
        self.busy = busy

    def get_name(self):
        return self.me.get_name()

    def get_interfaces(self, interface_type):
        result = []
        gatewayConfiguration = self.me.get_Configuration()
        gatewayInterfaces = gatewayConfiguration.get_GatewayInterfaces()
        gatewayInterfaces = filter(
            lambda gatewayInterface: gatewayInterface.get_InterfaceType() == interface_type,
            gatewayInterfaces.get_GatewayInterface())
        for gatewayInterface in gatewayInterfaces:
            result.append(gatewayInterface)
        return result

    def get_public_ips(self):
        result = []
        for gatewayInterface in self.get_interfaces('uplink'):
            for subnetParticipation in gatewayInterface.get_SubnetParticipation():
                ipRanges = subnetParticipation.get_IpRanges()
                if ipRanges:
                    for ipRange in ipRanges.get_IpRange():
                        startAddress = ipRange.get_StartAddress()
                        endAddress = ipRange.get_EndAddress()
                        addresses = IpRange(startAddress, endAddress)
                        for address in addresses:
                            result.append(address)
        result = list(set(result))
        return result

    def get_nat_rules(self):
        result = []
        gatewayConfiguration = self.me.get_Configuration()
        edgeGatewayServiceConfiguration = gatewayConfiguration.get_EdgeGatewayServiceConfiguration()
        natServiceList = filter(
            lambda service: service.__class__.__name__ == "NatServiceType",
            edgeGatewayServiceConfiguration.get_NetworkService())
        if len(natServiceList) > 0:
            natRules = natServiceList[0].get_NatRule()
            for natRule in natRules:
                result.append(natRule)
        return result

    def _post_nat_rules(self, new_rules, new_port=-1):
        pass

    def save_services_configuration(self):
        edgeGatewayServiceConfiguration = self.me.get_Configuration(
        ).get_EdgeGatewayServiceConfiguration()
        body = '<?xml version="1.0" encoding="UTF-8"?>' + \
               CommonUtils.convertPythonObjToStr(self.me.get_Configuration().get_EdgeGatewayServiceConfiguration(),
                                                 name='EdgeGatewayServiceConfiguration',
                                                 namespacedef='xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ')
        content_type = "application/vnd.vmware.admin.edgeGatewayServiceConfiguration+xml"
        link = filter(lambda link: link.get_type() ==
                      content_type, self.me.get_Link())
        self.response = Http.post(
            link[0].get_href(),
            data=body,
            headers=self.headers,
            verify=self.verify,
            logger=self.logger)
        if self.response.status_code == requests.codes.accepted:
            task = taskType.parseString(self.response.content, True)
            return task

    def add_nat_rules(self):
        pass

    def _select_gateway_interface(self, interface):
        if interface:
            interface = interface.lower()
            gatewayInterfaces = [
                i for i in (
                    self.get_interfaces('internal') +
                    self.get_interfaces('uplink')) if i.Name.lower() == interface]
        else:
            gatewayInterfaces = self.get_interfaces('uplink')
        if len(gatewayInterfaces):
            return gatewayInterfaces[0]
        return None

    def add_nat_rule(
            self,
            rule_type,
            original_ip,
            original_port,
            translated_ip,
            translated_port,
            protocol,
            interface=None):
        gatewayInterface = self._select_gateway_interface(interface)
        if not gatewayInterface:
            return
        natRules = self.get_nat_rules()

        maxId = 0
        minId = 65537
        for natRule in natRules:
            ruleId = natRule.get_Id()
            if ruleId > maxId:
                maxId = ruleId
            if ruleId < minId:
                minId = ruleId
        if maxId == 0:
            maxId = minId - 1

        port_changed = True
        original_port_modified = original_port
        while port_changed and len(natRules) > 0:
            for natRule in natRules:
                port_changed = False
                if rule_type == natRule.get_RuleType():
                    gatewayNatRule = natRule.get_GatewayNatRule()
                    if original_ip == gatewayNatRule.get_OriginalIp() and \
                       original_port_modified == gatewayNatRule.get_OriginalPort():
                        original_port_modified = str(
                            int(original_port_modified) + 1)
                        port_changed = True
                        break

        rule = NatRuleType()
        rule.set_RuleType(rule_type)
        rule.set_IsEnabled(True)
        # note, the new id has to be greater than the last
        # apparently the same id can be reused by two different rules, but use
        # a new one
        rule.set_Id(maxId + 1)
        gatewayRule = GatewayNatRuleType()
        gatewayInterfaceReference = ReferenceType()
        gatewayInterfaceReference.set_href(
            gatewayInterface.get_Network().get_href())
        gatewayInterfaceReference.set_type(
            gatewayInterface.get_Network().get_type())
        gatewayInterfaceReference.set_name(
            gatewayInterface.get_Network().get_name())
        gatewayRule.set_Interface(gatewayInterfaceReference)
        gatewayRule.set_OriginalIp(original_ip)
        gatewayRule.set_OriginalPort(original_port_modified)
        gatewayRule.set_TranslatedIp(translated_ip)
        gatewayRule.set_TranslatedPort(translated_port)
        gatewayRule.set_Protocol(protocol)
        rule.set_GatewayNatRule(gatewayRule)
        natRules.append(rule)
        natService = None
        edgeGatewayServiceConfiguration = self.me.get_Configuration(
        ).get_EdgeGatewayServiceConfiguration()
        natServices = filter(
            lambda service: service.__class__.__name__ == "NatServiceType",
            edgeGatewayServiceConfiguration.get_NetworkService())
        if len(natServices) > 0:
            natService = natServices[0]
            natService.set_NatRule(natRules)
        else:
            natService = NatServiceType(IsEnabled=True)
            natService.original_tagname_ = 'NatService'
            natService.set_NatRule(natRules)
            edgeGatewayServiceConfiguration.get_NetworkService().append(natService)

    def del_nat_rule(
            self,
            rule_type,
            original_ip,
            original_port,
            translated_ip,
            translated_port,
            protocol,
            interface=None):
        gatewayInterface = self._select_gateway_interface(interface)
        if not gatewayInterface:
            return
        if not interface:
            interface = gatewayInterface.get_Network().get_name()
        interface = interface.lower()
        natRules = self.get_nat_rules()
        newRules = []
        found_rule = False
        for natRule in natRules:
            if rule_type == natRule.get_RuleType():
                gatewayNatRule = natRule.get_GatewayNatRule()
                gateway_interface_name = gatewayNatRule.get_Interface().get_name().lower()
                gateway_original_ip = gatewayNatRule.get_OriginalIp(
                ) if gatewayNatRule.get_OriginalIp() else 'any'
                gateway_original_port = gatewayNatRule.get_OriginalPort(
                ) if gatewayNatRule.get_OriginalPort() else 'any'
                gateway_translated_ip = gatewayNatRule.get_TranslatedIp(
                ) if gatewayNatRule.get_TranslatedIp() else 'any'
                gateway_translated_port = gatewayNatRule.get_TranslatedPort(
                ) if gatewayNatRule.get_TranslatedPort() else 'any'
                gateway_protocol = gatewayNatRule.get_Protocol(
                ) if gatewayNatRule.get_Protocol() else 'any'
                if original_ip == gateway_original_ip and \
                   original_port == gateway_original_port and \
                   translated_ip == gateway_translated_ip and \
                   translated_port == gateway_translated_port and \
                   protocol == gateway_protocol and \
                   interface == gateway_interface_name:
                    found_rule = True
                else:
                    newRules.append(natRule)
            else:
                newRules.append(natRule)
        if found_rule:
            natService = None
            edgeGatewayServiceConfiguration = self.me.get_Configuration(
            ).get_EdgeGatewayServiceConfiguration()
            natServices = filter(
                lambda service: service.__class__.__name__ == "NatServiceType",
                edgeGatewayServiceConfiguration.get_NetworkService())
            if len(natServices) > 0:
                natService = natServices[0]
                natService.set_NatRule(newRules)
            else:
                natService = NatServiceType()
                natService.set_NatRule(newRules)
                edgeGatewayServiceConfiguration.get_NetworkService().append(natService)
            return True

    def del_all_nat_rules(self):
        natRules = self.get_nat_rules()
        newRules = []
        natService = None
        edgeGatewayServiceConfiguration = self.me.get_Configuration(
        ).get_EdgeGatewayServiceConfiguration()
        natServices = filter(
            lambda service: service.__class__.__name__ == "NatServiceType",
            edgeGatewayServiceConfiguration.get_NetworkService())
        if len(natServices) > 0:
            natService = natServices[0]
            natService.set_NatRule(newRules)
        else:
            natService = NatServiceType()
            natService.set_NatRule(newRules)
            edgeGatewayServiceConfiguration.get_NetworkService().append(natService)
        return True

    def is_fw_enabled(self):
        edgeGatewayServiceConfiguration = self.me.get_Configuration(
        ).get_EdgeGatewayServiceConfiguration()
        if edgeGatewayServiceConfiguration is None:
            return False
        services = filter(
            lambda service: service.__class__.__name__ == "FirewallServiceType",
            edgeGatewayServiceConfiguration.get_NetworkService())
        return len(services) == 1 and services[0].get_IsEnabled()

    def is_dhcp_enabled(self):
        edgeGatewayServiceConfiguration = self.me.get_Configuration(
        ).get_EdgeGatewayServiceConfiguration()
        if edgeGatewayServiceConfiguration is None:
            return False
        services = filter(
            lambda service: service.__class__.__name__ == "GatewayDhcpServiceType",
            edgeGatewayServiceConfiguration.get_NetworkService())
        return len(services) == 1 and services[0].get_IsEnabled()

    def is_nat_enabled(self):
        edgeGatewayServiceConfiguration = self.me.get_Configuration(
        ).get_EdgeGatewayServiceConfiguration()
        if edgeGatewayServiceConfiguration is None:
            return False
        services = filter(
            lambda service: service.__class__.__name__ == "NatServiceType",
            edgeGatewayServiceConfiguration.get_NetworkService())
        return len(services) == 1 and services[0].get_IsEnabled()

    def enable_fw(self, enable):
        edgeGatewayServiceConfiguration = self.me.get_Configuration(
        ).get_EdgeGatewayServiceConfiguration()
        services = filter(
            lambda service: service.__class__.__name__ == "FirewallServiceType",
            edgeGatewayServiceConfiguration.get_NetworkService())
        if len(services) == 1:
            services[0].set_IsEnabled(enable)

    def is_vpn_enabled(self):
        edgeGatewayServiceConfiguration = self.me.get_Configuration(
        ).get_EdgeGatewayServiceConfiguration()
        if edgeGatewayServiceConfiguration is None:
            return False
        services = filter(
            lambda service: service.__class__.__name__ == "GatewayIpsecVpnServiceType",
            edgeGatewayServiceConfiguration.get_NetworkService())
        return len(services) == 1 and services[0].get_IsEnabled()

    def add_vpn_service(self, IsEnabled=True):
        vpn_service = GatewayIpsecVpnServiceType(IsEnabled=IsEnabled)
        vpn_service.original_tagname_ = 'GatewayIpsecVpnService'
        edgeGatewayServiceConfiguration = self.me.get_Configuration(
        ).get_EdgeGatewayServiceConfiguration()
        edgeGatewayServiceConfiguration.get_NetworkService().append(vpn_service)
        return vpn_service

    def enable_vpn(self, enable):
        edgeGatewayServiceConfiguration = self.me.get_Configuration(
        ).get_EdgeGatewayServiceConfiguration()
        services = filter(
            lambda service: service.__class__.__name__ == "GatewayIpsecVpnServiceType",
            edgeGatewayServiceConfiguration.get_NetworkService())
        if len(services) == 0:
            vpn_service = self.add_vpn_service(enable)
            return vpn_service
        elif len(services) == 1:
            services[0].set_IsEnabled(enable)
            return services[0]
        else:
            return None

    def get_vpn_service(self):
        gatewayConfiguration = self.me.get_Configuration()
        edgeGatewayServiceConfiguration = gatewayConfiguration.get_EdgeGatewayServiceConfiguration()
        service = filter(
            lambda service: service.__class__.__name__ == "GatewayIpsecVpnServiceType",
            edgeGatewayServiceConfiguration.get_NetworkService())
        if service is not None and len(service) > 0:
            return service[0]

    def add_vpn_tunnel(
            self,
            name,
            local_ip,
            local_network_name,
            peer_ip,
            peer_network,
            secret):
        vpn_service = self.get_vpn_service()
        if vpn_service is None:
            vpn_service = self.add_vpn_service()
        peer = IpsecVpnThirdPartyPeerType(PeerId=peer_ip)
        peer.original_tagname_ = 'IpsecVpnThirdPartyPeer'

        interfaces = self.get_interfaces('internal')
        gateway_interface = None
        for interface in interfaces:
            if local_network_name == interface.get_Name():
                gateway_interface = interface
                break
        assert gateway_interface

        local_subnet = IpsecVpnSubnetType()
        local_subnet.set_Name(gateway_interface.get_Name())
        local_subnet.set_Gateway(
            gateway_interface.get_SubnetParticipation()[0].get_Gateway())
        local_subnet.set_Netmask(
            gateway_interface.get_SubnetParticipation()[0].get_Netmask())

        peer_subnet = IpsecVpnSubnetType()
        peer_subnet.set_Name(peer_network)
        pn = IPNetwork(peer_network)
        peer_subnet.set_Gateway(str(pn.ip))
        peer_subnet.set_Netmask(str(pn.netmask))

        tunnel = GatewayIpsecVpnTunnelType(
            Name=name, Description='',
            LocalIpAddress=local_ip, LocalId=local_ip,
            PeerIpAddress=peer_ip, PeerId=peer_ip,
            SharedSecret=secret, SharedSecretEncrypted=False,
            EncryptionProtocol='AES256', Mtu=1500,
            IsEnabled=True)
        tunnel.set_IpsecVpnPeer(peer)
        tunnel.add_LocalSubnet(local_subnet)
        tunnel.add_PeerSubnet(peer_subnet)
        vpn_service.add_Tunnel(tunnel)

    def delete_vpn_tunnel(self, name):
        vpn_service = self.get_vpn_service()
        if vpn_service is None or vpn_service.Endpoint is None:
            return False
        new_tunnels = []
        for tunnel in vpn_service.Tunnel:
            if tunnel.get_Name() != name:
                new_tunnels.append(tunnel)
        if len(vpn_service.Tunnel) == len(new_tunnels):
            return False
        vpn_service.Tunnel = new_tunnels
        return True

    def add_network_to_vpn_tunnel(
            self,
            name,
            local_network_name=None,
            peer_network=None):
        vpn_service = self.get_vpn_service()
        if vpn_service is None or vpn_service.Endpoint is None:
            return False
        for tunnel in vpn_service.Tunnel:
            if tunnel.get_Name() == name:
                if local_network_name is not None:
                    interfaces = self.get_interfaces('internal')
                    gateway_interface = None
                    for interface in interfaces:
                        if local_network_name == interface.get_Name():
                            gateway_interface = interface
                            break
                    local_subnet = IpsecVpnSubnetType()
                    local_subnet.set_Name(gateway_interface.get_Name())
                    local_subnet.set_Gateway(
                        gateway_interface.get_SubnetParticipation()[0].get_Gateway())
                    local_subnet.set_Netmask(
                        gateway_interface.get_SubnetParticipation()[0].get_Netmask())
                    tunnel.add_LocalSubnet(local_subnet)
                if peer_network is not None:
                    peer_subnet = IpsecVpnSubnetType()
                    peer_subnet.set_Name(peer_network)
                    pn = IPNetwork(peer_network)
                    peer_subnet.set_Gateway(str(pn.ip))
                    peer_subnet.set_Netmask(str(pn.netmask))
                    tunnel.add_PeerSubnet(peer_subnet)
                return True
        return False

    def delete_network_from_vpn_tunnel(
            self,
            name,
            local_network_name=None,
            peer_network=None):
        vpn_service = self.get_vpn_service()
        if vpn_service is None or vpn_service.Endpoint is None:
            return False
        for tunnel in vpn_service.Tunnel:
            if tunnel.get_Name() == name:
                if local_network_name is not None:
                    new_subnets = []
                    for subnet in tunnel.get_LocalSubnet():
                        if subnet.get_Name() != local_network_name:
                            new_subnets.append(subnet)
                    tunnel.set_LocalSubnet(new_subnets)
                if peer_network is not None:
                    new_subnets = []
                    for subnet in tunnel.get_PeerSubnet():
                        if subnet.get_Name() != peer_network:
                            new_subnets.append(subnet)
                    tunnel.set_PeerSubnet(new_subnets)
                return True
        return False

    def add_vpn_endpoint(self, network_name, public_ip):
        vpn_service = self.get_vpn_service()
        if vpn_service is None:
            vpn_service = self.add_vpn_service()
        interfaces = self.get_interfaces('uplink')
        network = None
        for interface in interfaces:
            if network_name == interface.get_Name():
                network = interface.get_Network()
                break
        assert network
        endpoint = GatewayIpsecVpnEndpointType(
            Network=network, PublicIp=public_ip)
        vpn_service.add_Endpoint(endpoint)

    def del_vpn_endpoint(self, network_name, public_ip):
        vpn_service = self.get_vpn_service()
        if vpn_service is None or vpn_service.Endpoint is None:
            return False
        interfaces = self.get_interfaces('uplink')
        network = None
        for interface in interfaces:
            if network_name == interface.get_Name():
                network = interface.get_Network()
                break
        assert network
        new_endpoints = []
        for endpoint in vpn_service.Endpoint:
            if (endpoint.Network.get_href() != network.get_href()) or (
                    endpoint.get_PublicIp() != public_ip):
                new_endpoints.append(endpoint)
        if len(vpn_service.Endpoint) == len(new_endpoints):
            return False
        vpn_service.Endpoint = new_endpoints

    def get_syslog_conf(self):
        headers = self.headers
        headers['Accept'] = 'application/*+xml;version=5.11'
        self.response = Http.get(
            self.me.href,
            data='',
            headers=headers,
            verify=self.verify,
            logger=self.logger)
        if self.response.status_code == requests.codes.ok:
            doc = ET.fromstring(self.response.content)
            for element in doc.iter(
                    '{http://www.vmware.com/vcloud/v1.5}SyslogServerIp'):
                return element.text
        return ''

    def set_syslog_conf(self, syslog_server_ip):
        headers = self.headers
        headers['Accept'] = 'application/*+xml;version=5.11'
        headers[
            'Content-Type'] = 'application/vnd.vmware.vcloud.SyslogSettings+xml;version=5.11'
        # content_type = "application/vnd.vmware.vcloud.SyslogSettings+xml"
        body = ''
        if '' == syslog_server_ip:
            body = """
            <SyslogServerSettings xmlns="http://www.vmware.com/vcloud/v1.5"
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.vmware.com/vcloud/v1.5 http://10.160.99.94/api/v1.5/schema/master.xsd">
                  <TenantSyslogServerSettings>
                  </TenantSyslogServerSettings>
              </SyslogServerSettings>
                    """
        else:
            body = """
            <SyslogServerSettings xmlns="http://www.vmware.com/vcloud/v1.5"
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.vmware.com/vcloud/v1.5 http://10.160.99.94/api/v1.5/schema/master.xsd">
                <TenantSyslogServerSettings>
                    <SyslogServerIp>%s</SyslogServerIp>
                </TenantSyslogServerSettings>
            </SyslogServerSettings>
            """ % syslog_server_ip
        # '<SyslogServerSettings><TenantSyslogServerSettings><SyslogServerIp>%s</SyslogServerIp></TenantSyslogServerSettings></SyslogServerSettings>' % syslog_server_ip
        # link = filter(lambda link: link.get_type() == content_type, self.me.get_Link())
        self.response = Http.post(
            self.me.href +
            '/action/configureSyslogServerSettings',
            data=body,
            headers=headers,
            verify=self.verify,
            logger=self.logger)
        if self.response.status_code == requests.codes.accepted:
            task = taskType.parseString(self.response.content, True)
            return task

    def _getFirewallService(self):
        gatewayConfiguration = self.me.get_Configuration()
        edgeGatewayServiceConfiguration = gatewayConfiguration.get_EdgeGatewayServiceConfiguration()
        return filter(
            lambda service: service.__class__.__name__ == "FirewallServiceType",
            edgeGatewayServiceConfiguration.get_NetworkService())[0]

    def get_fw_rules(self):
        return self._getFirewallService().get_FirewallRule()

    def add_fw_rule(
            self,
            is_enable,
            description,
            policy,
            protocol,
            dest_port,
            dest_ip,
            source_port,
            source_ip,
            enable_logging):
        protocols = _create_protocols_type(protocol)
        new_rule = FirewallRuleType(
            IsEnabled=is_enable,
            Description=description,
            Policy=policy,
            Protocols=protocols,
            DestinationPortRange=dest_port,
            DestinationIp=dest_ip,
            SourcePortRange=source_port,
            SourceIp=source_ip,
            EnableLogging=enable_logging)
        rules = self.get_fw_rules()
        rules.append(new_rule)
        self._getFirewallService().set_FirewallRule(rules)

    def delete_fw_rule(self, protocol, dest_port, dest_ip,
                       source_port, source_ip):
        def create_protocol_tuple(protocol):
            return (protocol.get_Tcp(),
                    protocol.get_Any(),
                    protocol.get_Udp(),
                    protocol.get_Icmp(),
                    protocol.get_Other())

        def compare(first, second):
            if isinstance(
                    first,
                    basestring) and isinstance(
                    second,
                    basestring):
                return first.lower() == second.lower()
            else:
                return first == second

        rules = self.get_fw_rules()
        new_rules = []
        to_delete_protocols = create_protocol_tuple(
            _create_protocols_type(protocol))
        for rule in rules:
            current_protocols = create_protocol_tuple(rule.get_Protocols())
            if (current_protocols == to_delete_protocols and
                compare(dest_port, rule.get_DestinationPortRange()) and
                compare(dest_ip, rule.get_DestinationIp()) and
                compare(source_port, rule.get_SourcePortRange()) and
                    compare(source_ip, rule.get_SourceIp())):
                continue
            else:
                new_rules.append(rule)
        self._getFirewallService().set_FirewallRule(new_rules)

    def _getDhcpService(self):
        edgeGatewayServiceConfiguration = self.me.get_Configuration(
        ).get_EdgeGatewayServiceConfiguration()
        dhcpServices = filter(
            lambda service: service.__class__.__name__ == "GatewayDhcpServiceType",
            edgeGatewayServiceConfiguration.get_NetworkService())
        if len(dhcpServices) > 0:
            return dhcpServices[0]

    def get_dhcp_service(self):
        return self._getDhcpService()

    def add_dhcp_service(self, IsEnabled=True):
        service = GatewayDhcpServiceType(IsEnabled=IsEnabled)
        service.original_tagname_ = 'GatewayDhcpService'
        edgeGatewayServiceConfiguration = self.me.get_Configuration(
        ).get_EdgeGatewayServiceConfiguration()
        edgeGatewayServiceConfiguration.get_NetworkService().append(service)
        return service

    def enable_dhcp(self, enable):
        edgeGatewayServiceConfiguration = self.me.get_Configuration(
        ).get_EdgeGatewayServiceConfiguration()
        services = filter(
            lambda service: service.__class__.__name__ == "GatewayDhcpServiceType",
            edgeGatewayServiceConfiguration.get_NetworkService())
        if len(services) == 0:
            dhcpService = self.add_dhcp_service(enable)
            return dhcpService
        elif len(services) == 1:
            services[0].set_IsEnabled(enable)
            return services[0]
        else:
            return None

    def get_dhcp_pools(self):
        service = self._getDhcpService()
        if service:
            return service.get_Pool()

    def add_dhcp_pool(self, network_name, low_ip_address, hight_ip_address,
                      default_lease, max_lease):
        if not default_lease:
            default_lease = DEFAULT_LEASE
        if not max_lease:
            max_lease = MAX_LEASE
        gatewayConfiguration = self.me.get_Configuration()
        network = filter(
            lambda interface: interface.get_Name() == network_name,
            gatewayConfiguration.get_GatewayInterfaces().get_GatewayInterface())[0].get_Network()
        network.set_type("application/vnd.vmware.vcloud.orgVdcNetwork+xml")

        new_pool = DhcpPoolServiceType(
            IsEnabled=True,
            Network=network,
            DefaultLeaseTime=default_lease,
            MaxLeaseTime=max_lease,
            LowIpAddress=low_ip_address,
            HighIpAddress=hight_ip_address)
        service = self._getDhcpService()
        if service is None:
            service = self.add_dhcp_service(IsEnabled=True)
        pools = self.get_dhcp_pools()
        if pools is None:
            pools = []
        pools.append(new_pool)
        service.set_Pool(pools)

    def delete_dhcp_pool(self, network_name):
        pools = [p for p in self.get_dhcp_pools(
        ) if p.get_Network().name != network_name]
        self._getDhcpService().set_Pool(pools)

    def allocate_public_ip(self):
        api_version = '5.11'
        headers = dict(self.headers)
        headers['Accept'] = 'application/*+xml;version={0}'.format(api_version)
        href = self.me.get_href() + '/action/manageExternalIpAddresses'
        body = """
        <ExternalIpAddressActionList
         xmlns="http://www.vmware.com/vcloud/networkservice/1.0">
        <Allocation>
            <NumberOfExternalIpAddressesToAllocate>1</NumberOfExternalIpAddressesToAllocate>
        </Allocation>
        </ExternalIpAddressActionList>
        """

        self.response = Http.put(href, data=body, headers=headers,
                                 verify=self.verify, logger=self.logger)
        if self.response.status_code == requests.codes.ok:
            task = taskType.parseString(self.response.content, True)
            return task

    def deallocate_public_ip(self, ip_address):
        api_version = '5.11'
        headers = dict(self.headers)
        headers['Accept'] = 'application/*+xml;version={0}'.format(api_version)
        href = self.me.get_href() + '/action/manageExternalIpAddresses'
        body = """
        <ExternalIpAddressActionList
         xmlns="http://www.vmware.com/vcloud/networkservice/1.0">
        <Deallocation>
            <ExternalIpAddress>{0}</ExternalIpAddress>
        </Deallocation>
        </ExternalIpAddressActionList>
        """.format(ip_address)

        self.response = Http.put(href, data=body, headers=headers,
                                 verify=self.verify, logger=self.logger)
        if self.response.status_code == requests.codes.ok:
            task = taskType.parseString(self.response.content, True)
            return task

    def is_busy(self):
        return self.busy


def _create_protocols_type(protocol):
    all_protocols = {"Tcp": None, "Udp": None, "Icmp": None, "Any": None}
    all_protocols[protocol] = True
    return ProtocolsType(**all_protocols)
