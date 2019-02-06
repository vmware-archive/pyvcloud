# VMware vCloud Director Python SDK
# Copyright (c) 2014-2019 VMware, Inc. All Rights Reserved.
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
import unittest
from uuid import uuid1
from pyvcloud.vcd.client import ApiVersion
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import TaskStatus
from pyvcloud.system_test_framework.base_test import BaseTestCase
from pyvcloud.system_test_framework.environment import CommonRoles
from pyvcloud.system_test_framework.environment import Environment
from pyvcloud.system_test_framework.constants.gateway_constants import \
    GatewayConstants
from pyvcloud.vcd.nat_rule import NatRule
from pyvcloud.vcd.gateway import Gateway
from pyvcloud.vcd.utils import netmask_to_cidr_prefix_len


class TestNatRule(BaseTestCase):
    """Test Nat Rule functionalities implemented in pyvcloud."""
    # All tests in this module should be run as System Administrator.
    _name = GatewayConstants.name
    _snat_action = 'snat'
    _snat_orig_addr = '2.2.3.7'
    _snat_trans_addr = '2.2.3.8'
    _new_snat_orig_addr = '2.2.3.13'
    _new_snat_trans_addr = '2.2.3.14'
    _new_snat_desc = 'SNAT Rule Edited'
    _dnat_action = 'dnat'
    _dnat1_orig_addr = '2.2.3.10'
    _dnat1_trans_addr = '2.2.3.11-2.2.3.12'
    _dnat1_protocol = 'tcp'
    _dnat1_orig_port = 80
    _dnat1_trans_port = 80
    _dnat2_orig_addr = '2.2.3.15'
    _dnat2_trans_addr = '2.2.3.16-2.2.3.17'
    _dnat2_protocol = 'icmp'
    _dnat2_desc = 'icmp protocol'

    def test_0000_setup(self):
        """Add the sub allocated ip pools to gateway.

        This sub allocated ip pools required by the Nat Rule

        Invokes the add_sub_allocated_ip_pools of the gateway.
        """
        TestNatRule._client = Environment.get_sys_admin_client()
        TestNatRule._config = Environment.get_config()
        gateway = Environment. \
            get_test_gateway(TestNatRule._client)
        gateway_obj = Gateway(TestNatRule._client,
                              TestNatRule._name,
                              href=gateway.get('href'))
        ip_allocations = gateway_obj.list_configure_ip_settings()
        ip_allocation = ip_allocations[0]
        ext_network = ip_allocation.get('external_network')
        config = TestNatRule._config['external_network']
        gateway_sub_allocated_ip_range = \
            config['gateway_sub_allocated_ip_range']
        ip_range_list = [gateway_sub_allocated_ip_range]

        task = gateway_obj.add_sub_allocated_ip_pools(ext_network,
                                                      ip_range_list)
        result = TestNatRule._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        gateway_obj = Gateway(TestNatRule._client,
                              TestNatRule._name,
                              href=gateway.get('href'))
        subnet_participation = self.__get_subnet_participation(
            gateway_obj.get_resource(), ext_network)
        ip_ranges = gateway_obj.get_sub_allocate_ip_ranges_element(
            subnet_participation)
        self.__validate_ip_range(ip_ranges, gateway_sub_allocated_ip_range)

    def __get_subnet_participation(self, gateway, ext_network):
        for gatewayinf in \
                gateway.Configuration.GatewayInterfaces.GatewayInterface:
            if gatewayinf.Name == ext_network:
                return gatewayinf.SubnetParticipation

    def __validate_ip_range(self, IpRanges, _ip_range1):
        """ Validate if the ip range present in the existing ip ranges """
        _ip_ranges = _ip_range1.split('-')
        _ip_range1_start_address = _ip_ranges[0]
        _ip_range1_end_address = _ip_ranges[1]
        for ip_range in IpRanges.IpRange:
            if ip_range.StartAddress == _ip_range1_start_address:
                self.assertEqual(ip_range.EndAddress, _ip_range1_end_address)

    def test_0010_add_nat_rule(self):
        """Add Nat Rule in the gateway.

        Invokes the add_nat_rule of the gateway.
        """
        gateway = Environment. \
            get_test_gateway(TestNatRule._client)
        gateway_obj = Gateway(TestNatRule._client,
                              TestNatRule._name,
                              href=gateway.get('href'))
        # Create SNAT Rule
        gateway_obj.add_nat_rule(
            action=TestNatRule._snat_action,
            original_address=TestNatRule._snat_orig_addr,
            translated_address=TestNatRule._snat_trans_addr)
        # Create DNAT Rule for tcp/udp protocol
        gateway_obj.add_nat_rule(
            action=TestNatRule._dnat_action,
            original_address=TestNatRule._dnat1_orig_addr,
            translated_address=TestNatRule._dnat1_trans_addr,
            protocol=TestNatRule._dnat1_protocol,
            original_port=TestNatRule._dnat1_orig_port,
            translated_port=TestNatRule._dnat1_trans_port)
        # Create DNAT Rule for icmp protocol
        gateway_obj.add_nat_rule(
            action=TestNatRule._dnat_action,
            original_address=TestNatRule._dnat2_orig_addr,
            translated_address=TestNatRule._dnat2_trans_addr,
            description=TestNatRule._dnat2_protocol,
            protocol=TestNatRule._dnat2_protocol)
        nat_rule = gateway_obj.get_nat_rules()
        #Verify
        snat_found = False
        dnat_found = False
        for natRule in nat_rule.natRules.natRule:
            if natRule.action == 'snat' and \
                natRule.originalAddress == TestNatRule._snat_orig_addr :
                snat_found = True
            if natRule.action == 'dnat' and \
                natRule.originalAddress == TestNatRule._dnat1_orig_addr :
                dnat_found = True
        self.assertTrue(snat_found)
        self.assertTrue(dnat_found)

    def test_0015_get_nat_rule_info(self):
        """Get the details of nat rule.

        Invokes the get_nat_rule_info of the NatRule.
        """
        gateway = Environment. \
            get_test_gateway(TestNatRule._client)
        gateway_obj = Gateway(TestNatRule._client,
                              TestNatRule._name,
                              href=gateway.get('href'))
        nat_rule = gateway_obj.get_nat_rules()
        rule_id = self.__get_snat_rule_id(nat_rule)
        nat_obj = NatRule(TestNatRule._client, self._name, rule_id)
        nat_rule_info =  nat_obj.get_nat_rule_info()
        #Verify
        self.assertTrue(len(nat_rule_info) > 0)
        self.assertEqual(nat_rule_info['Action'], TestNatRule._snat_action)
        self.assertEqual(nat_rule_info['OriginalAddress'],
                         TestNatRule._snat_orig_addr)

    def test_0020_list_nat_rules(self):
        """List all nat rules on a gateway.

        Invokes the list_nat_rules of the Gateway.
        """
        gateway = Environment. \
            get_test_gateway(TestNatRule._client)
        gateway_obj = Gateway(TestNatRule._client,
                              TestNatRule._name,
                              href=gateway.get('href'))
        nat_rule_list = gateway_obj.list_nat_rules()
        #Verify
        self.assertTrue(len(nat_rule_list) > 0)

    def test_0025_reorder_nat_rule(self):
        """Reorder the nat rule position on gateway.

        Invokes the reorder_nat_rule of the Gateway.
        """
        gateway = Environment. \
            get_test_gateway(TestNatRule._client)
        gateway_obj = Gateway(TestNatRule._client,
                              TestNatRule._name,
                              href=gateway.get('href'))
        nat_rule = gateway_obj.get_nat_rules()
        rule_id = self.__get_snat_rule_id(nat_rule)
        index1 = self.__get_snat_rule_index(nat_rule)
        new_index = 2
        gateway_obj.reorder_nat_rule(rule_id, new_index)
        nat_rule = gateway_obj.get_nat_rules()
        index2 = self.__get_snat_rule_index(nat_rule)
        self.assertNotEqual(index1, index2)

    def test_0030_update_nat_rule(self):
        """Update a Nat Rule.

        Invokes the update_nat_rule of the NatRule.
        """
        gateway = Environment. \
            get_test_gateway(TestNatRule._client)
        gateway_obj = Gateway(TestNatRule._client,
                              TestNatRule._name,
                              href=gateway.get('href'))
        nat_rule = gateway_obj.get_nat_rules()
        rule_id = self.__get_snat_rule_id(nat_rule)
        nat_obj = NatRule(TestNatRule._client, self._name, rule_id)
        nat_obj.update_nat_rule(
            original_address=TestNatRule._new_snat_orig_addr,
            translated_address=TestNatRule._new_snat_trans_addr,
            description=TestNatRule._new_snat_desc)
        #Verify
        nat_rule = gateway_obj.get_nat_rules()
        match_found = False
        for natRule in nat_rule.natRules.natRule:
            if natRule.originalAddress == TestNatRule._new_snat_orig_addr and \
                natRule.translatedAddress == TestNatRule._new_snat_trans_addr and \
                natRule.description == TestNatRule._new_snat_desc:
                match_found = True
        self.assertTrue(match_found)

    def __get_snat_rule_id(self, nat_rule):
        """ Get the ID of Nat Rule"""
        for natRule in nat_rule.natRules.natRule:
            if natRule.action == TestNatRule._snat_action:
                rule_id = natRule.ruleId
                break
        return rule_id

    def __get_snat_rule_index(self, nat_rule):
        """ Get the index of SNAT Rule"""
        for natRule in nat_rule.natRules.natRule:
            if natRule.action == TestNatRule._snat_action:
                index = nat_rule.natRules.index(natRule)
                break
        return index

    def test_0090_delete_nat_rule(self):
        """Delete Nat Rule in the gateway.

        Invokes the delete_nat_rule of the NatRule.
        """
        gateway = Environment. \
            get_test_gateway(TestNatRule._client)
        gateway_obj = Gateway(TestNatRule._client,
                              TestNatRule._name,
                              href=gateway.get('href'))
        nat_rule = gateway_obj.get_nat_rules()

        nat_objects = []
        for natRule in nat_rule.natRules.natRule:
            nat_objects.append(
                NatRule(TestNatRule._client, self._name, natRule.ruleId))

        for nat_object in nat_objects:
            nat_object.delete_nat_rule()
        #Verify
        nat_rule = gateway_obj.get_nat_rules()
        self.assertFalse(hasattr(nat_rule.natRules, 'natRule'))

    def test_0098_teardown(self):
        """Remove the sub allocated ip pools of gateway.

        Invokes the remove_sub_allocated_ip_pools of the gateway.
        """
        gateway = Environment. \
            get_test_gateway(TestNatRule._client)
        gateway_obj = Gateway(TestNatRule._client,
                              TestNatRule._name,
                              href=gateway.get('href'))
        ip_allocations = gateway_obj.list_configure_ip_settings()
        ip_allocation = ip_allocations[0]
        ext_network = ip_allocation.get('external_network')
        config = TestNatRule._config['external_network']
        gateway_sub_allocated_ip_range1 = \
            config['gateway_sub_allocated_ip_range']

        task = gateway_obj.remove_sub_allocated_ip_pools(ext_network,
                                             [gateway_sub_allocated_ip_range1])
        result = TestNatRule._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        gateway = Environment. \
            get_test_gateway(TestNatRule._client)
        gateway_obj = Gateway(TestNatRule._client,
                              TestNatRule._name,
                              href=gateway.get('href'))
        subnet_participation = self.__get_subnet_participation(
            gateway_obj.get_resource(), ext_network)
        """removed the IpRanges form subnet_participation."""
        self.assertFalse(hasattr(subnet_participation, 'IpRanges'))

    def test_0099_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestNatRule._client.logout()


if __name__ == '__main__':
    unittest.main()
