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
from pyvcloud.system_test_framework.base_test import BaseTestCase
from pyvcloud.system_test_framework.environment import Environment
from pyvcloud.system_test_framework.constants.gateway_constants import \
    GatewayConstants
from pyvcloud.vcd.gateway import Gateway


class TestFirewallRules(BaseTestCase):
    """Test firewall rules functionalities implemented in pyvcloud."""
    # All tests in this module should be run as System Administrator.
    # Firewall Rule
    _firewall_rule_name = 'Rule Name Test'
    _name = GatewayConstants.name

    def test_0000_setup(self):
        """Add Firewall Rules in the gateway.

        Invokes the add_firewall_rule of the gateway.
        """
        TestFirewallRules._client = Environment.get_sys_admin_client()
        TestFirewallRules._config = Environment.get_config()
        gateway = Environment. \
            get_test_gateway(TestFirewallRules._client)
        gateway_obj = Gateway(TestFirewallRules._client,
                              TestFirewallRules._name,
                              href=gateway.get('href'))
        gateway_obj.add_firewall_rule(TestFirewallRules._firewall_rule_name)
        firewall_rules_resource = gateway_obj.get_firewall_rules()
        # Verify
        matchFound = False
        for firewallRule in firewall_rules_resource.firewallRules.firewallRule:
            if firewallRule['name'] == TestFirewallRules._firewall_rule_name:
                matchFound = True
                break
        self.assertTrue(matchFound)

    def test_0001_list_firewall_rules(self):
        """List Firewall Rules of the gateway.

        Invokes the get_firewall_rules_list of the gateway.
        """
        TestFirewallRules._config = Environment.get_config()
        gateway = Environment. \
            get_test_gateway(TestFirewallRules._client)
        gateway_obj = Gateway(TestFirewallRules._client,
                              TestFirewallRules._name,
                              href=gateway.get('href'))
        firewall_rules_list = gateway_obj.get_firewall_rules_list()
        # Verify
        self.assertTrue(len(firewall_rules_list) > 0)

    def test_0098_teardown(self):
        pass


    def test_0099_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestFirewallRules._client.logout()


if __name__ == '__main__':
    unittest.main()
