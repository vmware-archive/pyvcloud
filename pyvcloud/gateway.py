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
from schema.vcd.v1_5.schemas.vcloud.networkType import NatRuleType, GatewayNatRuleType, ReferenceType, NatServiceType, FirewallRuleType, ProtocolsType, DhcpPoolServiceType
from iptools import IpRange
from helper import CommonUtils
from xml.etree import ElementTree as ET

DEFAULT_LEASE = 3600
MAX_LEASE = 7200

class Gateway(object):

    def __init__(self, gateway, headers, verify):
        self.me = gateway
        self.headers = headers
        self.verify = verify
        self.response = None

    def get_name(self):
        return self.me.get_name()

    def get_interfaces(self, interface_type):
        result = []
        gatewayConfiguration = self.me.get_Configuration()
        gatewayInterfaces = gatewayConfiguration.get_GatewayInterfaces()
        gatewayInterfaces = filter(lambda gatewayInterface: gatewayInterface.get_InterfaceType() == interface_type, gatewayInterfaces.get_GatewayInterface())
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
        natServiceList = filter(lambda service: service.__class__.__name__ == "NatServiceType", edgeGatewayServiceConfiguration.get_NetworkService())
        if len(natServiceList) > 0:
            natRules = natServiceList[0].get_NatRule()
            for natRule in natRules:
                result.append(natRule)
        return result

    def _post_nat_rules(self, new_rules, new_port=-1):
        pass

    def save_services_configuration(self):
        edgeGatewayServiceConfiguration = self.me.get_Configuration().get_EdgeGatewayServiceConfiguration()
        body = '<?xml version="1.0" encoding="UTF-8"?>' + \
               CommonUtils.convertPythonObjToStr(self.me.get_Configuration().get_EdgeGatewayServiceConfiguration(),
                                                 name='EdgeGatewayServiceConfiguration',
                                                 namespacedef='xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ')
        content_type = "application/vnd.vmware.admin.edgeGatewayServiceConfiguration+xml"
        link = filter(lambda link: link.get_type() == content_type, self.me.get_Link())
        self.response = requests.post(link[0].get_href(), data=body, headers=self.headers)     
        if self.response.status_code == requests.codes.accepted:
            task = taskType.parseString(self.response.content, True)
            return task           

    def add_nat_rules(self):
        pass

    def add_nat_rule(self, rule_type, original_ip, original_port, translated_ip, translated_port, protocol):
        gatewayInterfaces = self.get_interfaces('uplink')
        if len(gatewayInterfaces) == 0:
            return
        gatewayInterface = gatewayInterfaces[0]
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
                        original_port_modified = str(int(original_port_modified) + 1)
                        port_changed = True
                        break

        rule = NatRuleType()
        rule.set_RuleType(rule_type)
        rule.set_IsEnabled(True)
        # note, the new id has to be greater than the last
        # apparently the same id can be reused by two different rules, but use a new one
        rule.set_Id(maxId + 1)
        gatewayRule = GatewayNatRuleType()
        gatewayInterfaceReference = ReferenceType()
        gatewayInterfaceReference.set_href(gatewayInterface.get_Network().get_href())
        gatewayInterfaceReference.set_type(gatewayInterface.get_Network().get_type())
        gatewayInterfaceReference.set_name(gatewayInterface.get_Network().get_name())

        gatewayRule.set_Interface(gatewayInterfaceReference)
        gatewayRule.set_OriginalIp(original_ip)
        gatewayRule.set_OriginalPort(original_port_modified)
        gatewayRule.set_TranslatedIp(translated_ip)
        gatewayRule.set_TranslatedPort(translated_port)
        gatewayRule.set_Protocol(protocol)
        rule.set_GatewayNatRule(gatewayRule)
        natRules.append(rule)
        natService = None
        edgeGatewayServiceConfiguration = self.me.get_Configuration().get_EdgeGatewayServiceConfiguration()
        natServices = filter(lambda service: service.__class__.__name__ == "NatServiceType", edgeGatewayServiceConfiguration.get_NetworkService())
        if len(natServices) > 0:
            natService = natServices[0]
            natService.set_NatRule(natRules)
        else:
            natService = NatServiceType()
            natService.set_NatRule(natRules)
            edgeGatewayServiceConfiguration.get_NetworkService().append(natService)

    def del_nat_rule(self, rule_type, original_ip, original_port, translated_ip, translated_port, protocol):
        gatewayInterfaces = self.get_interfaces('uplink')
        if len(gatewayInterfaces) == 0:
            return False
        gatewayInterface = gatewayInterfaces[0]
        natRules = self.get_nat_rules()
        newRules = []

        found_rule = False
        for natRule in natRules:
            # todo check if the network interface is the same
            ruleId = natRule.get_Id()
            if rule_type == natRule.get_RuleType():
                gatewayNatRule = natRule.get_GatewayNatRule()
                # import sys; gatewayNatRule.export(sys.stdout, 0)
                gateway_original_ip = gatewayNatRule.get_OriginalIp() if gatewayNatRule.get_OriginalIp() else 'any'
                gateway_original_port = gatewayNatRule.get_OriginalPort() if gatewayNatRule.get_OriginalPort() else 'any'
                gateway_translated_ip = gatewayNatRule.get_TranslatedIp() if gatewayNatRule.get_TranslatedIp() else 'any'
                gateway_translated_port = gatewayNatRule.get_TranslatedPort() if gatewayNatRule.get_TranslatedPort() else 'any'
                gateway_protocol = gatewayNatRule.get_Protocol() if gatewayNatRule.get_Protocol() else 'any'
                if original_ip == gateway_original_ip and \
                   original_port == gateway_original_port and \
                   translated_ip == gateway_translated_ip and \
                   translated_port == gateway_translated_port and \
                   protocol == gateway_protocol:
                    found_rule = True
                else:
                    newRules.append(natRule)
            else:
                newRules.append(natRule)
        # return self._post_nat_rules(newRules)
        if found_rule:
            natService = None
            edgeGatewayServiceConfiguration = self.me.get_Configuration().get_EdgeGatewayServiceConfiguration()
            natServices = filter(lambda service: service.__class__.__name__ == "NatServiceType", edgeGatewayServiceConfiguration.get_NetworkService())
            if len(natServices) > 0:
                natService = natServices[0]
                natService.set_NatRule(newRules)
            else:
                natService = NatServiceType()
                natService.set_NatRule(newRules)
                edgeGatewayServiceConfiguration.get_NetworkService().append(natService)
            # import sys; self.me.export(sys.stdout, 0)
            return True

    def del_all_nat_rules(self):
        gatewayInterfaces = self.get_interfaces('uplink')
        if len(gatewayInterfaces) == 0:
            return False
        gatewayInterface = gatewayInterfaces[0]
        natRules = self.get_nat_rules()
        newRules = []

        natService = None
        edgeGatewayServiceConfiguration = self.me.get_Configuration().get_EdgeGatewayServiceConfiguration()
        natServices = filter(lambda service: service.__class__.__name__ == "NatServiceType", edgeGatewayServiceConfiguration.get_NetworkService())
        if len(natServices) > 0:
            natService = natServices[0]
            natService.set_NatRule(newRules)
        else:
            natService = NatServiceType()
            natService.set_NatRule(newRules)
            edgeGatewayServiceConfiguration.get_NetworkService().append(natService)
        return True

    def is_fw_enabled(self):
        edgeGatewayServiceConfiguration = self.me.get_Configuration().get_EdgeGatewayServiceConfiguration()
        services = filter(lambda service: service.__class__.__name__ == "FirewallServiceType", edgeGatewayServiceConfiguration.get_NetworkService())
        return len(services) == 1 and services[0].get_IsEnabled()

    def is_dhcp_enabled(self):
        edgeGatewayServiceConfiguration = self.me.get_Configuration().get_EdgeGatewayServiceConfiguration()
        services = filter(lambda service: service.__class__.__name__ == "GatewayDhcpServiceType", edgeGatewayServiceConfiguration.get_NetworkService())
        return len(services) == 1 and services[0].get_IsEnabled()

    def is_nat_enabled(self):
        edgeGatewayServiceConfiguration = self.me.get_Configuration().get_EdgeGatewayServiceConfiguration()
        services = filter(lambda service: service.__class__.__name__ == "NatServiceType", edgeGatewayServiceConfiguration.get_NetworkService())
        return len(services) == 1 and services[0].get_IsEnabled()

    def enable_fw(self, enable):
        edgeGatewayServiceConfiguration = self.me.get_Configuration().get_EdgeGatewayServiceConfiguration()
        services = filter(lambda service: service.__class__.__name__ == "FirewallServiceType", edgeGatewayServiceConfiguration.get_NetworkService())
        if len(services) == 1:
            services[0].set_IsEnabled(enable)

    def get_syslog_conf(self):
        headers = self.headers
        headers['Accept']='application/*+xml;version=5.11'
        self.response = requests.get(self.me.href, data='', headers=headers, verify=self.verify)
        if self.response.status_code == requests.codes.ok:
            doc = ET.fromstring(self.response.content)
            for element in doc.iter('{http://www.vmware.com/vcloud/v1.5}SyslogServerIp'):
                return element.text
        return ''

    def set_syslog_conf(self, syslog_server_ip):
        headers = self.headers
        headers['Accept'] = 'application/*+xml;version=5.11'
        headers['Content-Type'] = 'application/vnd.vmware.vcloud.SyslogSettings+xml;version=5.11'
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
        self.response = requests.post(self.me.href+'/action/configureSyslogServerSettings', data=body, headers=headers, verify=self.verify)     
        if self.response.status_code == requests.codes.accepted:
            task = taskType.parseString(self.response.content, True)
            return task           

    def _getFirewallService(self):
        gatewayConfiguration = self.me.get_Configuration()
        edgeGatewayServiceConfiguration = gatewayConfiguration.get_EdgeGatewayServiceConfiguration()
        return filter(lambda service: service.__class__.__name__ == "FirewallServiceType",
                      edgeGatewayServiceConfiguration.get_NetworkService())[0]

    def get_fw_rules(self):
        return self._getFirewallService().get_FirewallRule()

    def add_fw_rule(self, is_enable, description, policy, protocol, dest_port, dest_ip,
                    source_port, source_ip, enable_logging):
        protocols = _create_protocols_type(protocol)
        new_rule = FirewallRuleType(IsEnabled=is_enable,
                                    Description=description, Policy=policy, Protocols=protocols,
                                    DestinationPortRange=dest_port, DestinationIp=dest_ip,
                                    SourcePortRange=source_port, SourceIp=source_ip,
                                    EnableLogging=enable_logging)
        rules = self.get_fw_rules()
        rules.append(new_rule)
        self._getFirewallService().set_FirewallRule(rules)

    def delete_fw_rule(self, protocol, dest_port, dest_ip,
                       source_port, source_ip):
        def create_protocol_list(protocol):
            plist = []
            plist.append(protocol.get_Tcp())
            plist.append(protocol.get_Any())
            plist.append(protocol.get_Tcp())
            plist.append(protocol.get_Udp())
            plist.append(protocol.get_Icmp())
            plist.append(protocol.get_Other())
            return plist

        rules = self.get_fw_rules()
        new_rules = []
        to_delete_trait = (create_protocol_list(_create_protocols_type(protocol)),
                           dest_port, dest_ip,
                           source_port, source_ip)
        for rule in rules:
            current_trait = (create_protocol_list(rule.get_Protocols()),
                             rule.get_DestinationPortRange(),
                             rule.get_DestinationIp(),
                             rule.get_SourcePortRange(),
                             rule.get_SourceIp())
            if current_trait == to_delete_trait:
                continue
            else:
                new_rules.append(rule)
        self._getFirewallService().set_FirewallRule(new_rules)

    def _getDhcpService(self):
        edgeGatewayServiceConfiguration = self.me.get_Configuration().get_EdgeGatewayServiceConfiguration()
        dhcpService = filter(lambda service: service.__class__.__name__ == "GatewayDhcpServiceType",
                             edgeGatewayServiceConfiguration.get_NetworkService())[0]
        return dhcpService

    def get_dhcp_pools(self):
        return self._getDhcpService().get_Pool()

    def add_dhcp_pool(self, network_name, low_ip_address, hight_ip_address,
                      default_lease, max_lease):
        if not default_lease:
            default_lease = DEFAULT_LEASE
        if not max_lease:
            max_lease = MAX_LEASE
        gatewayConfiguration = self.me.get_Configuration()
        network = filter(lambda interface: interface.get_Name() == network_name,
                         gatewayConfiguration.get_GatewayInterfaces().get_GatewayInterface())[0].get_Network()
        network.set_type("application/vnd.vmware.vcloud.orgVdcNetwork+xml")

        new_pool = DhcpPoolServiceType(IsEnabled=True, Network=network, DefaultLeaseTime=default_lease,
                                       MaxLeaseTime=max_lease,
                                       LowIpAddress=low_ip_address,
                                       HighIpAddress=hight_ip_address)
        pools = self.get_dhcp_pools()
        pools.append(new_pool)
        self._getDhcpService().set_Pool(pools)

    def delete_dhcp_pool(self, network_name):
        pools = [p for p in self.get_dhcp_pools() if p.get_Network().name != network_name]
        self._getDhcpService().set_Pool(pools)

def _create_protocols_type(protocol):
    all_protocols = {"Tcp": None, "Udp": None, "Icmp": None, "Any": None}
    all_protocols[protocol] = True
    return ProtocolsType(**all_protocols)
