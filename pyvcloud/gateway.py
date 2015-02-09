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
from schema.vcd.v1_5.schemas.vcloud import networkType, vdcType, queryRecordViewType, taskType
from schema.vcd.v1_5.schemas.vcloud.networkType import NatRuleType, GatewayNatRuleType, ReferenceType
from iptools import ipv4, IpRange
from tabulate import tabulate
from helper import CommonUtils

class Gateway(object):

    def __init__(self, gateway, headers, verify):
        self.me = gateway
        self.headers = headers
        self.verify = verify
        
    def get_name(self):
        return self.me.get_name()
        
    def get_interfaces(self, interface_type):
        result = []
        gatewayConfiguration = self.me.get_Configuration()
        gatewayInterfaces = gatewayConfiguration.get_GatewayInterfaces()
        gatewayInterfaces = filter(lambda gatewayInterface : gatewayInterface.get_InterfaceType() == interface_type, gatewayInterfaces.get_GatewayInterface())
        for gatewayInterface in gatewayInterfaces:
            result.append(gatewayInterface)
        return result
        
    def get_public_ips(self):
        result = []        
        for gatewayInterface in self.get_interfaces('uplink'):
            subnetParticipation = gatewayInterface.get_SubnetParticipation()[0]
            ipRanges = subnetParticipation.get_IpRanges()
            if ipRanges:
                for ipRange in ipRanges.get_IpRange():
                    startAddress = ipRange.get_StartAddress()
                    endAddress = ipRange.get_EndAddress()
                    addresses = IpRange(startAddress, endAddress)
                    for address in addresses:
                        result.append(address)
            # ipAddress = subnetParticipation.get_IpAddress()
            # if ipAddress: result.append(ipAddress)
        result = list(set(result))
        return result
        
    def get_nat_rules(self):
        result = []
        gatewayConfiguration = self.me.get_Configuration()
        edgeGatewayServiceConfiguration = gatewayConfiguration.get_EdgeGatewayServiceConfiguration()
        natServiceList = filter(lambda service: service.__class__.__name__ == "NatServiceType" , edgeGatewayServiceConfiguration.get_NetworkService())
        if len(natServiceList)>0:
            natRules = natServiceList[0].get_NatRule()
            for natRule in natRules:
                result.append(natRule)
        return result
        
    def get_fw_rules(self):
        pass
        
    def _post_nat_rules(self, new_rules, new_port=-1):
        pass
        
    def save_services_configuration(self):
        edgeGatewayServiceConfiguration = self.me.get_Configuration().get_EdgeGatewayServiceConfiguration()
        body = '<?xml version="1.0" encoding="UTF-8"?>' + \
            CommonUtils.convertPythonObjToStr(self.me.get_Configuration().get_EdgeGatewayServiceConfiguration(), 
            name = 'EdgeGatewayServiceConfiguration',
            namespacedef = 'xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ')
        content_type = "application/vnd.vmware.admin.edgeGatewayServiceConfiguration+xml"
        link = filter(lambda link: link.get_type() == content_type, self.me.get_Link())
        response = requests.post(link[0].get_href(), data=body, headers=self.headers)     
        if response.status_code == requests.codes.accepted:
            task = taskType.parseString(response.content, True)
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
        while port_changed and len(natRules)>0:     
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
        natService = None
        edgeGatewayServiceConfiguration = self.me.get_Configuration().get_EdgeGatewayServiceConfiguration()        
        natServices = filter(lambda service: service.__class__.__name__ == "NatServiceType" , edgeGatewayServiceConfiguration.get_NetworkService())
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
            #todo check if the network interface is the same
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
            natServices = filter(lambda service: service.__class__.__name__ == "NatServiceType" , edgeGatewayServiceConfiguration.get_NetworkService())
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
        natServices = filter(lambda service: service.__class__.__name__ == "NatServiceType" , edgeGatewayServiceConfiguration.get_NetworkService())
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
        services = filter(lambda service: service.__class__.__name__ == "FirewallServiceType" , edgeGatewayServiceConfiguration.get_NetworkService())
        return len(services) == 1 and services[0].get_IsEnabled()
        
    def is_dhcp_enabled(self):
        edgeGatewayServiceConfiguration = self.me.get_Configuration().get_EdgeGatewayServiceConfiguration()
        services = filter(lambda service: service.__class__.__name__ == "GatewayDhcpServiceType" , edgeGatewayServiceConfiguration.get_NetworkService())
        return len(services) == 1 and services[0].get_IsEnabled()
        
    def is_nat_enabled(self):
        edgeGatewayServiceConfiguration = self.me.get_Configuration().get_EdgeGatewayServiceConfiguration()
        services = filter(lambda service: service.__class__.__name__ == "NatServiceType" , edgeGatewayServiceConfiguration.get_NetworkService())
        return len(services) == 1 and services[0].get_IsEnabled()
            
    def enable_fw(self, enable):
        edgeGatewayServiceConfiguration = self.me.get_Configuration().get_EdgeGatewayServiceConfiguration()
        services = filter(lambda service: service.__class__.__name__ == "FirewallServiceType" , edgeGatewayServiceConfiguration.get_NetworkService())
        if len(services) == 1:
            services[0].set_IsEnabled(enable)
        