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

DEFAULT_LEASE = 3600
MAX_LEASE = 7200


import requests
from schema.vcd.v1_5.schemas.vcloud import networkType, vdcType, queryRecordViewType, taskType
from schema.vcd.v1_5.schemas.vcloud.networkType import NatRuleType, GatewayNatRuleType, ReferenceType, DhcpPoolServiceType
from pyvcloud.schema.vcd.v1_5.schemas.vcloud.networkType import FirewallRuleType, ProtocolsType
from iptools import ipv4, IpRange
from tabulate import tabulate
from helper import generalHelperFunctions as ghf

class Gateway(object):

    def __init__(self, gateway, headers):
        self.me = gateway
        self.headers = headers

    def get_name(self):
        return self.me.get_name()

    def get_uplink_interfaces(self):
        result = []
        gatewayConfiguration = self.me.get_Configuration()
        gatewayInterfaces = gatewayConfiguration.get_GatewayInterfaces()
        gatewayInterfaces = filter(lambda gatewayInterface : gatewayInterface.get_InterfaceType() == "uplink", gatewayInterfaces.get_GatewayInterface())
        for gatewayInterface in gatewayInterfaces:
            result.append(gatewayInterface)
        return result

    def get_public_ips(self):
        result = []
        for gatewayInterface in self.get_uplink_interfaces():
            subnetParticipation = gatewayInterface.get_SubnetParticipation()[0]
            ipRanges = subnetParticipation.get_IpRanges()
            for ipRange in ipRanges.get_IpRange():
                startAddress = ipRange.get_StartAddress()
                endAddress = ipRange.get_EndAddress()
                addresses = IpRange(startAddress, endAddress)
                for address in addresses:
                    result.append(address)
        return result

    def get_nat_rules(self):
        result = []
        gatewayConfiguration = self.me.get_Configuration()
        edgeGatewayServiceConfiguration = gatewayConfiguration.get_EdgeGatewayServiceConfiguration()
        natService = filter(lambda service: service.__class__.__name__ == "NatServiceType" , edgeGatewayServiceConfiguration.get_NetworkService())[0]
        natRules = natService.get_NatRule()
        for natRule in natRules:
            result.append(natRule)
        return result

    def _post_nat_rules(self, new_rules, new_port=-1):
        edgeGatewayServiceConfiguration = self.me.get_Configuration().get_EdgeGatewayServiceConfiguration()
        natService = filter(lambda service: service.__class__.__name__ == "NatServiceType" , edgeGatewayServiceConfiguration.get_NetworkService())[0]
        natService.set_NatRule(new_rules)
        body = '<?xml version="1.0" encoding="UTF-8"?>' + \
            ghf.convertPythonObjToStr(self.me.get_Configuration().get_EdgeGatewayServiceConfiguration(), name = 'EdgeGatewayServiceConfiguration',
                                      namespacedef = 'xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ')
        content_type = "application/vnd.vmware.admin.edgeGatewayServiceConfiguration+xml"
        # get link element that contains an action URL for instantiateVAppTemplate.
        # It implements an action that adds an object (a vApp) to the VDC.
        link = filter(lambda link: link.get_type() == content_type, self.me.get_Link())
        # send post request using this body as data
        # does it need to specify the content type? No
        response = requests.post(link[0].get_href(), data=body, headers=self.headers)
        if response.status_code == requests.codes.accepted:
            task = taskType.parseString(response.content, True)
            return (True, task, new_port)
        else:
            return (False, response.content, -1)

    def add_nat_rules(self):
        pass

    def add_nat_rule(self, rule_type, original_ip, original_port, translated_ip, translated_port, protocol):
        gatewayInterfaces = self.get_uplink_interfaces()
        if len(gatewayInterfaces) == 0:
            return (False, None)
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
        while port_changed:
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
        #note, the new id has to be greater than the last
        #apparently the same id can be reused by two different rules, but use a new one
        rule.set_Id(maxId+1)
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
        return self._post_nat_rules(natRules, original_port_modified)

    def del_nat_rule(self, rule_type, original_ip, original_port, translated_ip, translated_port, protocol):
        gatewayInterfaces = self.get_uplink_interfaces()
        if len(gatewayInterfaces) == 0:
            return (False, None)
        gatewayInterface = gatewayInterfaces[0]
        natRules = self.get_nat_rules()
        newRules = []

        for natRule in natRules:
            #todo check if the network interface is the same
            ruleId = natRule.get_Id()
            if rule_type == natRule.get_RuleType():
                gatewayNatRule = natRule.get_GatewayNatRule()
                if original_ip == gatewayNatRule.get_OriginalIp() and \
                   original_port == gatewayNatRule.get_OriginalPort() and \
                   translated_ip == gatewayNatRule.get_TranslatedIp() and \
                   translated_port == gatewayNatRule.get_TranslatedPort() and \
                   protocol == gatewayNatRule.get_Protocol():
                   pass
                else:
                   newRules.append(natRule)
            else:
                newRules.append(natRule)
        return self._post_nat_rules(newRules)

    def del_all_nat_rules(self):
        pass

    def enable_fw(self, enable):
        pass

    def get_dhcp_pools(self):
        gatewayConfiguration = self.me.get_Configuration()
        edgeGatewayServiceConfiguration = gatewayConfiguration.get_EdgeGatewayServiceConfiguration()
        dhcpService = filter(lambda service: service.__class__.__name__ == "GatewayDhcpServiceType",
                             edgeGatewayServiceConfiguration.get_NetworkService())[0]
        return dhcpService.get_Pool()

    def _post_configuration(self):
        gatewayConfiguration = self.me.get_Configuration()
        edgeGatewayServiceConfiguration = gatewayConfiguration.get_EdgeGatewayServiceConfiguration()
        body = '<?xml version="1.0" encoding="UTF-8"?>' + \
               ghf.convertPythonObjToStr(edgeGatewayServiceConfiguration, name='EdgeGatewayServiceConfiguration',
                                         namespacedef='xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ')
        content_type = "application/vnd.vmware.admin.edgeGatewayServiceConfiguration+xml"
        link = filter(lambda link: link.get_type() == content_type, self.me.get_Link())
        content_type = "application/vnd.vmware.admin.edgeGatewayServiceConfiguration+xml"
        self.headers["Content-Type"] = content_type
        response = requests.post(link[0].get_href(), data=body, headers=self.headers)
        if response.status_code == requests.codes.accepted:
            task = taskType.parseString(response.content, True)
            return (True, task)
        else:
            return (False, response.content)

    def _post_dhcp_pools(self, pools):
        gatewayConfiguration = self.me.get_Configuration()
        edgeGatewayServiceConfiguration = gatewayConfiguration.get_EdgeGatewayServiceConfiguration()
        dhcpService = filter(lambda service: service.__class__.__name__ == "GatewayDhcpServiceType",
                             edgeGatewayServiceConfiguration.get_NetworkService())[0]
        dhcpService.set_Pool(pools)
        return self._post_configuration()

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
        return self._post_dhcp_pools(pools)

    def delete_dhcp_pool(self, network_name):
        pools = [p for p in self.get_dhcp_pools() if p.get_Network().name != network_name]
        return self._post_dhcp_pools(pools)

    def _getFirewallService(self):
        gatewayConfiguration = self.me.get_Configuration()
        edgeGatewayServiceConfiguration = gatewayConfiguration.get_EdgeGatewayServiceConfiguration()
        return filter(lambda service: service.__class__.__name__ == "FirewallServiceType",
                      edgeGatewayServiceConfiguration.get_NetworkService())[0]

    def _post_firewall_rules(self, rules):
        self._getFirewallService().set_FirewallRule(rules)
        return self._post_configuration()

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
        return self._post_firewall_rules(rules)

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
        return self._post_firewall_rules(new_rules)


def _create_protocols_type(protocol):
    all_protocols = {"Tcp": None, "Udp": None, "Icmp": None, "Any": None}
    all_protocols[protocol] = True
    return ProtocolsType(**all_protocols)
