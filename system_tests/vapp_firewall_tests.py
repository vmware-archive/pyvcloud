# VMware vCloud Director Python SDK
# Copyright (c) 2014-2019 VMware, Inc. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from pyvcloud.system_test_framework.base_test import BaseTestCase
from pyvcloud.vcd.vapp_firewall import VappFirewall
from pyvcloud.system_test_framework.vapp_constants import VAppConstants
from pyvcloud.system_test_framework.environment import Environment
from pyvcloud.system_test_framework.environment import developerModeAware
from pyvcloud.vcd.client import TaskStatus
from pyvcloud.vcd.client import FenceMode


class TestVappFirewall(BaseTestCase):
    """Test vapp dhcp functionalities implemented in pyvcloud."""
    _vapp_name = VAppConstants.name
    _network_name = VAppConstants.network1_name
    _enable = True
    _disable = False
    _drop = 'drop'
    _allow = 'allow'
    _test_firewall_rule_name = 'test_firewall_rule'
    _org_vdc_network_name = 'test-direct-vdc-network'
    _update_firewall_rule_name = 'updated_firewall_rule'

    def test_0000_setup(self):
        TestVappFirewall._client = Environment.get_sys_admin_client()
        vapp = Environment.get_test_vapp_with_network(TestVappFirewall._client)
        vapp.reload()
        task = vapp.connect_vapp_network_to_ovdc_network(
            network_name=TestVappFirewall._network_name,
            orgvdc_network_name=TestVappFirewall._org_vdc_network_name)
        result = TestVappFirewall._client.get_task_monitor().wait_for_success(
            task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0012_enable_firewall_service(self):
        vapp_firewall = VappFirewall(
            TestVappFirewall._client,
            vapp_name=TestVappFirewall._vapp_name,
            network_name=TestVappFirewall._network_name)
        # disable firewall service
        task = vapp_firewall.enable_firewall_service(TestVappFirewall._disable)
        result = TestVappFirewall._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        vapp_firewall._reload()
        firewall_service = \
            vapp_firewall.resource.Configuration.Features.FirewallService
        self.assertFalse(firewall_service.IsEnabled)
        # enable firewall service
        task = vapp_firewall.enable_firewall_service(TestVappFirewall._enable)
        TestVappFirewall._client.get_task_monitor().wait_for_success(task=task)
        vapp_firewall._reload()
        firewall_service = \
            vapp_firewall.resource.Configuration.Features.FirewallService
        self.assertTrue(firewall_service.IsEnabled)

    def test_0020_set_default_action(self):
        vapp_firewall = VappFirewall(
            TestVappFirewall._client,
            vapp_name=TestVappFirewall._vapp_name,
            network_name=TestVappFirewall._network_name)
        # set allow as default action and True log of firewall service
        task = vapp_firewall.set_default_action(TestVappFirewall._allow,
                                                TestVappFirewall._enable)
        result = TestVappFirewall._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        vapp_firewall._reload()
        firewall_service = \
            vapp_firewall.resource.Configuration.Features.FirewallService
        self.assertEqual(TestVappFirewall._allow,
                         firewall_service.DefaultAction)
        self.assertTrue(firewall_service.LogDefaultAction)

    def test_0030_add_firewall_rule(self):
        vapp_firewall = VappFirewall(
            TestVappFirewall._client,
            vapp_name=TestVappFirewall._vapp_name,
            network_name=TestVappFirewall._network_name)
        task = vapp_firewall.add_firewall_rule(
            name=TestVappFirewall._test_firewall_rule_name)
        result = TestVappFirewall._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        vapp_firewall._reload()
        firewall_service = \
            vapp_firewall.resource.Configuration.Features.FirewallService
        self.assertTrue(hasattr(firewall_service, 'FirewallRule'))
        self.assertEqual(TestVappFirewall._test_firewall_rule_name,
                         firewall_service.FirewallRule[1].Description)

    def test_0040_list_firewall_rule(self):
        vapp_firewall = VappFirewall(
            TestVappFirewall._client,
            vapp_name=TestVappFirewall._vapp_name,
            network_name=TestVappFirewall._network_name)
        result = vapp_firewall.list_firewall_rule()
        self.assertNotEqual(len(result), 0)
        self.assertTrue(any(
            d['Name'] == TestVappFirewall._test_firewall_rule_name for d in
            result))

    def test_0050_update_firewall_rule(self):
        vapp_firewall = VappFirewall(
            TestVappFirewall._client,
            vapp_name=TestVappFirewall._vapp_name,
            network_name=TestVappFirewall._network_name)
        task = vapp_firewall.update_firewall_rule(
            name=TestVappFirewall._test_firewall_rule_name,
            new_name=TestVappFirewall._update_firewall_rule_name)
        result = TestVappFirewall._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        vapp_firewall._reload()
        firewall_service = \
            vapp_firewall.resource.Configuration.Features.FirewallService
        self.assertTrue(hasattr(firewall_service, 'FirewallRule'))
        self.assertEqual(TestVappFirewall._update_firewall_rule_name,
                         firewall_service.FirewallRule[1].Description)

        task = vapp_firewall.update_firewall_rule(
            name=TestVappFirewall._update_firewall_rule_name,
            new_name=TestVappFirewall._test_firewall_rule_name)
        result = TestVappFirewall._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0060_delete_firewall_rule(self):
        vapp_firewall = VappFirewall(
            TestVappFirewall._client,
            vapp_name=TestVappFirewall._vapp_name,
            network_name=TestVappFirewall._network_name)
        task = vapp_firewall.delete_firewall_rule(
            TestVappFirewall._test_firewall_rule_name)
        result = TestVappFirewall._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        vapp_firewall._reload()
        result = vapp_firewall.list_firewall_rule()
        self.assertFalse(any(
            d['Name'] == TestVappFirewall._test_firewall_rule_name for d in
            result))

    @developerModeAware
    def test_9998_teardown(self):
        """Test the  method vdc.delete_vapp().

        Invoke the method for all the vApps created by setup.

        This test passes if all the tasks for deleting the vApps succeed.
        """
        vdc = Environment.get_test_vdc(TestVappFirewall._client)
        task = vdc.delete_vapp(name=TestVappFirewall._vapp_name, force=True)
        result = TestVappFirewall._client.get_task_monitor().wait_for_success(
            task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_9999_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestVappFirewall._client.logout()


if __name__ == '__main__':
    unittest.main()
