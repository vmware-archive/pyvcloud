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
from pyvcloud.system_test_framework.base_test import BaseTestCase
from pyvcloud.system_test_framework.environment import Environment
from pyvcloud.system_test_framework.constants.gateway_constants import \
    GatewayConstants
from pyvcloud.system_test_framework.constants.ovdc_network_constant import \
    OvdcNetConstants
from pyvcloud.vcd.firewall_rule import FirewallRule
from pyvcloud.vcd.gateway import Gateway
from pyvcloud.system_test_framework.environment import CommonRoles


class TestFirewallRules(BaseTestCase):
    """Test firewall rules functionalities implemented in pyvcloud."""
    # All tests in this module should be run as System Administrator.
    # Firewall Rule
    _firewall_rule_name = 'Rule Name Test' + str(uuid1())
    _firewall_rule_name2 = 'Rule Name Test2' + str(uuid1())
    _name = GatewayConstants.name
    _rule_id = None
    _test_runner_role = CommonRoles.ORGANIZATION_ADMINISTRATOR

    def test_0000_setup(self):
        """Add Firewall Rules in the gateway.

        Invokes the add_firewall_rule of the gateway.
        """
        TestFirewallRules._org_client = Environment.get_client_in_default_org(
            TestFirewallRules._test_runner_role)
        TestFirewallRules._system_client = Environment.get_sys_admin_client()
        TestFirewallRules._config = Environment.get_config()
        gateway = Environment.get_test_gateway(TestFirewallRules._org_client)
        TestFirewallRules._gateway_obj = Gateway(
            TestFirewallRules._org_client,
            TestFirewallRules._name,
            href=gateway.get('href'))
        TestFirewallRules._external_network = Environment. \
            get_test_external_network(TestFirewallRules._system_client)

        TestFirewallRules._gateway_obj.add_firewall_rule(
            TestFirewallRules._firewall_rule_name)
        firewall_rules_resource = \
            TestFirewallRules._gateway_obj.get_firewall_rules()

        # Verify
        matchFound = False
        for firewallRule in firewall_rules_resource.firewallRules.firewallRule:
            if firewallRule['name'] == TestFirewallRules._firewall_rule_name:
                TestFirewallRules._rule_id = firewallRule.id
                matchFound = True
                break
        self.assertTrue(matchFound)

    def test_0001_list_firewall_rules(self):
        """List Firewall Rules of the gateway.

        Invokes the get_firewall_rules_list of the gateway.
        """
        TestFirewallRules._config = Environment.get_config()
        gateway = Environment. \
            get_test_gateway(TestFirewallRules._org_client)
        gateway_obj = Gateway(
            TestFirewallRules._org_client,
            TestFirewallRules._name,
            href=gateway.get('href'))
        firewall_rules_list = gateway_obj.get_firewall_rules_list()
        # Verify
        self.assertTrue(len(firewall_rules_list) > 0)

    def test_0010_get_created_firewall_rule(self):
        """Get the Firewall Rule created in setup."""
        firewall_obj = FirewallRule(TestFirewallRules._org_client,
                                    TestFirewallRules._name,
                                    TestFirewallRules._rule_id)
        firewall_res = firewall_obj._get_resource()
        self.assertIsNotNone(firewall_res)

    def test_0020_list_source_objects(self):
        object_res = TestFirewallRules._gateway_obj.list_firewall_objects(
            'source', 'gatewayinterface')
        if object_res:
            self.assertTrue(len(object_res) > 0)

        object_res = TestFirewallRules._gateway_obj.list_firewall_objects(
            'source', 'virtualmachine')
        if object_res:
            self.assertTrue(len(object_res) > 0)

        object_res = TestFirewallRules._gateway_obj.list_firewall_objects(
            'source', 'ipset')

    def test_0030_list_destination_objects(self):
        object_res = TestFirewallRules._gateway_obj.list_firewall_objects(
            'destination', 'gatewayinterface')
        if object_res:
            self.assertTrue(len(object_res) > 0)

        object_res = TestFirewallRules._gateway_obj.list_firewall_objects(
            'destination', 'virtualmachine')
        if object_res:
            self.assertTrue(len(object_res) > 0)

    def test_0040_list_object_types(self):
        object_res = TestFirewallRules._gateway_obj.list_firewall_object_types(
            'destination')
        if object_res:
            self.assertTrue(len(object_res) > 0)

        object_res = \
            TestFirewallRules._gateway_obj.list_firewall_object_types('source')
        if object_res:
            self.assertTrue(len(object_res) > 0)

    def test_0050_edit(self):
        firewall_obj = FirewallRule(TestFirewallRules._org_client,
                                    TestFirewallRules._name,
                                    TestFirewallRules._rule_id)
        ext_net_resource = TestFirewallRules._external_network.get_resource()
        source_object = [
            ext_net_resource.get('name') + ':gatewayinterface',
            OvdcNetConstants.routed_net_name + ':network', '2.3.2.2:ip'
        ]
        destination_object = [
            ext_net_resource.get('name') + ':gatewayinterface',
            OvdcNetConstants.routed_net_name + ':network', '2.3.2.2:ip'
        ]
        source = [{
            'tcp': {
                'any': 'any'
            }
        }, {
            'icmp': {
                'any': 'any'
            }
        }, {
            'any': {
                'any': 'any'
            }
        }]
        new_name = 'Rule_New_Name_Test'
        firewall_obj.edit(source_object, destination_object, source, new_name)
        # Verify
        firewall_obj._reload()
        firewall_res = firewall_obj.resource
        self.assertTrue(hasattr(firewall_res.source, 'vnicGroupId'))
        self.assertTrue(hasattr(firewall_res.source, 'groupingObjectId'))
        self.assertTrue(hasattr(firewall_res.source, 'ipAddress'))
        self.assertTrue(hasattr(firewall_res.destination, 'vnicGroupId'))
        self.assertTrue(hasattr(firewall_res.destination, 'groupingObjectId'))
        self.assertTrue(hasattr(firewall_res.destination, 'ipAddress'))
        self.assertTrue(hasattr(firewall_res.application, 'service'))
        self.assertEqual(firewall_res.name, 'Rule_New_Name_Test')
        # revert back name change to old name
        firewall_obj.edit(source_object, destination_object, source,
                          TestFirewallRules._firewall_rule_name)

    def test_0041_enable_disable_firewall_rule(self):
        firewall_obj = FirewallRule(TestFirewallRules._org_client,
                                    TestFirewallRules._name,
                                    TestFirewallRules._rule_id)
        result = firewall_obj.enable_disable_firewall_rule(False)
        self.assertIsNone(result)
        result = firewall_obj.enable_disable_firewall_rule(True)
        self.assertIsNone(result)

    def test_0061_info_firewall_rule(self):
        firewall_obj = FirewallRule(TestFirewallRules._org_client,
                                    TestFirewallRules._name,
                                    TestFirewallRules._rule_id)
        firewall_rule_info = firewall_obj.info_firewall_rule()
        # Verify
        self.assertTrue(len(firewall_rule_info) > 0)
        self.assertEqual(firewall_rule_info['Id'], TestFirewallRules._rule_id)

    def test_0081_list_firewall_rule_source(self):
        firewall_obj = FirewallRule(TestFirewallRules._org_client,
                                    TestFirewallRules._name,
                                    TestFirewallRules._rule_id)
        result = firewall_obj.list_firewall_rule_source_destination('source')
        self.assertTrue('vnicGroupId' in result)
        self.assertTrue('groupingObjectId' in result)
        self.assertTrue('ipAddress' in result)
        self.assertTrue('exclude' in result)

    def test_0082_list_firewall_rule_destination(self):
        firewall_obj = FirewallRule(TestFirewallRules._org_client,
                                    TestFirewallRules._name,
                                    TestFirewallRules._rule_id)
        result = firewall_obj.list_firewall_rule_source_destination(
            'destination')
        self.assertTrue('vnicGroupId' in result)
        self.assertTrue('groupingObjectId' in result)
        self.assertTrue('ipAddress' in result)
        self.assertTrue('exclude' in result)

    def test_0083_list_firewall_rule_service(self):
        firewall_obj = FirewallRule(TestFirewallRules._org_client,
                                    TestFirewallRules._name,
                                    TestFirewallRules._rule_id)
        result = firewall_obj.list_firewall_rule_service()
        self.assertTrue(len(result) > 0)
        self.assertTrue('Protocol' in result[0])

    def test_0091_update_firewall_rule_sequence(self):
        TestFirewallRules._gateway_obj.add_firewall_rule(
            TestFirewallRules._firewall_rule_name2)
        firewall_rules_resource = \
            TestFirewallRules._gateway_obj.get_firewall_rules()
        rule_id = None
        for firewallRule in firewall_rules_resource.firewallRules.firewallRule:
            if firewallRule['name'] == TestFirewallRules._firewall_rule_name2:
                rule_id = firewallRule.id
                break

        firewall_obj = FirewallRule(TestFirewallRules._org_client,
                                    TestFirewallRules._name, rule_id)
        new_index = 1
        firewall_obj.update_firewall_rule_sequence(new_index)
        sequence_no_after = 0
        firewall_rules_resource = \
            TestFirewallRules._gateway_obj.get_firewall_rules()
        for firewallRule in firewall_rules_resource.firewallRules.firewallRule:
            if firewallRule['name'] == TestFirewallRules._firewall_rule_name2:
                break
            sequence_no_after += 1
        self.assertEqual(sequence_no_after, new_index)
        firewall_obj.delete()

    def test_0095_delete_firewall_rule_source(self):
        object_to_delete = 'vnic-0'
        firewall_obj = FirewallRule(TestFirewallRules._org_client,
                                    TestFirewallRules._name,
                                    TestFirewallRules._rule_id)
        # deleting of object
        firewall_obj.delete_firewall_rule_source_destination(
            object_to_delete, 'source')
        list_of_values = firewall_obj.list_firewall_rule_source_destination(
            'source')
        if 'vnicGroupId' in list_of_values:
            self.assertTrue(
                object_to_delete not in list_of_values['vnicGroupId'])

    def test_0096_delete_firewall_rule_destination(self):
        object_to_delete = 'vnic-0'
        firewall_obj = FirewallRule(TestFirewallRules._org_client,
                                    TestFirewallRules._name,
                                    TestFirewallRules._rule_id)
        # deleting of object
        firewall_obj.delete_firewall_rule_source_destination(
            object_to_delete, 'destination')
        list_of_values = \
            firewall_obj.list_firewall_rule_source_destination(
                'destination')
        if 'vnicGroupId' in list_of_values:
            self.assertTrue(
                object_to_delete not in list_of_values['vnicGroupId'])

    def test_0097_delete_firewall_rule_service(self):
        object_to_delete = 'tcp'
        firewall_obj = FirewallRule(TestFirewallRules._org_client,
                                    TestFirewallRules._name,
                                    TestFirewallRules._rule_id)
        firewall_obj.delete_firewall_rule_service(object_to_delete)
        list_of_services = firewall_obj.list_firewall_rule_service()
        self.assertFalse(
            any(object_to_delete in service for service in list_of_services))

    def test_0098_teardown(self):
        firewall_obj = FirewallRule(TestFirewallRules._org_client,
                                    TestFirewallRules._name,
                                    TestFirewallRules._rule_id)
        firewall_obj.delete()
        # Verify
        firewall_rules_resource = \
            TestFirewallRules._gateway_obj.get_firewall_rules()

        # Verify
        matchFound = False
        for firewallRule in firewall_rules_resource.firewallRules.firewallRule:
            if firewallRule['id'] == TestFirewallRules._rule_id:
                matchFound = True
                break
        self.assertFalse(matchFound)

    def test_0099_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestFirewallRules._org_client.logout()


if __name__ == '__main__':
    unittest.main()
