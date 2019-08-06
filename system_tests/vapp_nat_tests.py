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
from pyvcloud.vcd.vapp_nat import VappNat
from pyvcloud.system_test_framework.vapp_constants import VAppConstants
from pyvcloud.system_test_framework.environment import Environment
from pyvcloud.system_test_framework.environment import developerModeAware
from pyvcloud.vcd.client import TaskStatus
from pyvcloud.vcd.client import FenceMode
from pyvcloud.vcd.client import IpAddressMode
from pyvcloud.vcd.client import NetworkAdapterType
from pyvcloud.vcd.vm import VM


class TestVappNat(BaseTestCase):
    """Test vapp dhcp functionalities implemented in pyvcloud."""
    _vapp_name = VAppConstants.name
    _network_name = VAppConstants.network1_name
    _vm_name = VAppConstants.vm1_name
    _org_vdc_network_name = 'test-direct-vdc-network'
    _enable = True
    _disable = False
    _nat_type_ip_translation = 'ipTranslation'
    _nat_type_port_forwarding = 'portForwarding'
    _policy_traffic = 'allowTraffic'
    _policy_traffic_in = 'allowTrafficIn'
    _allocate_ip_address = '90.80.70.10'
    _rule_id = '65537'
    _ext_ip_addr = '2.2.3.20'
    _manual = 'manual'

    def test_0000_setup(self):
        TestVappNat._client = Environment.get_sys_admin_client()
        vapp = Environment.get_test_vapp_with_network(TestVappNat._client)
        vapp.reload()
        task = vapp.connect_vapp_network_to_ovdc_network(
            network_name=TestVappNat._network_name,
            orgvdc_network_name=TestVappNat._org_vdc_network_name)
        result = TestVappNat._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        vm_resource = vapp.get_vm(TestVappNat._vm_name)
        vm = VM(TestVappNat._client, resource=vm_resource)
        task = vm.add_nic(NetworkAdapterType.E1000.value, True, True,
                          TestVappNat._network_name,
                          IpAddressMode.MANUAL.value,
                          TestVappNat._allocate_ip_address)
        result = TestVappNat._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        list_vm_interface = vapp.list_vm_interface(TestVappNat._network_name)
        for vm_interface in list_vm_interface:
            TestVappNat._vm_id = str(vm_interface['Local_id'])
            TestVappNat._vm_nic_id = str(vm_interface['VmNicId'])

    def test_0010_enable_nat_service(self):
        vapp_nat = VappNat(TestVappNat._client,
                           vapp_name=TestVappNat._vapp_name,
                           network_name=TestVappNat._network_name)
        # disable NAT service
        task = vapp_nat.enable_nat_service(TestVappNat._disable)
        result = TestVappNat._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        vapp_nat._reload()
        nat_service = vapp_nat.resource.Configuration.Features.NatService
        self.assertFalse(nat_service.IsEnabled)
        # enable NAT service
        task = vapp_nat.enable_nat_service(TestVappNat._enable)
        result = TestVappNat._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        vapp_nat._reload()
        nat_service = vapp_nat.resource.Configuration.Features.NatService
        self.assertTrue(nat_service.IsEnabled)

    def test_0020_update_nat_type(self):
        vapp_nat = VappNat(TestVappNat._client,
                           vapp_name=TestVappNat._vapp_name,
                           network_name=TestVappNat._network_name)
        task = vapp_nat.update_nat_type(TestVappNat._nat_type_port_forwarding,
                                        TestVappNat._policy_traffic)
        result = TestVappNat._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        vapp_nat._reload()
        nat_service = vapp_nat.resource.Configuration.Features.NatService
        self.assertEqual(nat_service.NatType,
                         TestVappNat._nat_type_port_forwarding)
        self.assertEqual(nat_service.Policy, TestVappNat._policy_traffic)
        # Revert back changes
        task = vapp_nat.update_nat_type(TestVappNat._nat_type_ip_translation,
                                        TestVappNat._policy_traffic_in)
        result = TestVappNat._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        vapp_nat._reload()
        self.assertEqual(nat_service.NatType,
                         TestVappNat._nat_type_ip_translation)
        self.assertEqual(nat_service.Policy, TestVappNat._policy_traffic_in)

    def test_0030_add_nat_rule(self):
        vapp_nat = VappNat(TestVappNat._client,
                           vapp_name=TestVappNat._vapp_name,
                           network_name=TestVappNat._network_name)
        task = vapp_nat.add_nat_rule(TestVappNat._nat_type_port_forwarding,
                                     vapp_scoped_vm_id=TestVappNat._vm_id,
                                     vm_nic_id=TestVappNat._vm_nic_id)
        result = TestVappNat._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        vapp_nat._reload()
        nat_service = vapp_nat.resource.Configuration.Features.NatService
        self.assertTrue(hasattr(nat_service.NatRule, 'VmRule'))
        task = vapp_nat.add_nat_rule(TestVappNat._nat_type_ip_translation,
                                     vapp_scoped_vm_id=TestVappNat._vm_id,
                                     vm_nic_id=TestVappNat._vm_nic_id)
        result = TestVappNat._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        vapp_nat._reload()
        nat_service = vapp_nat.resource.Configuration.Features.NatService
        self.assertTrue(hasattr(nat_service.NatRule, 'OneToOneVmRule'))

    def test_0040_get_nat_type(self):
        vapp_nat = VappNat(TestVappNat._client,
                           vapp_name=TestVappNat._vapp_name,
                           network_name=TestVappNat._network_name)
        result = vapp_nat.get_nat_type()
        self.assertEqual(result['NatType'],
                         TestVappNat._nat_type_ip_translation)
        self.assertEqual(result['Policy'], TestVappNat._policy_traffic_in)

    def test_0050_get_list_of_nat_rule(self):
        vapp_nat = VappNat(TestVappNat._client,
                           vapp_name=TestVappNat._vapp_name,
                           network_name=TestVappNat._network_name)
        result = vapp_nat.get_list_of_nat_rule()
        self.assertEqual(result[0]['VAppScopedVmId'], TestVappNat._vm_id)
        self.assertEqual(str(result[0]['VmNicId']), TestVappNat._vm_nic_id)

    def test_0060_update_nat_rule(self):
        vapp_nat = VappNat(TestVappNat._client,
                           vapp_name=TestVappNat._vapp_name,
                           network_name=TestVappNat._network_name)
        task = vapp_nat.update_nat_rule(
            rule_id=TestVappNat._rule_id,
            mapping_mode=TestVappNat._manual,
            external_ip_address=TestVappNat._ext_ip_addr)
        result = TestVappNat._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        vapp_nat._reload()
        nat_service = vapp_nat.resource.Configuration.Features.NatService
        one_to_one_rule = nat_service.NatRule.OneToOneVmRule
        self.assertEqual(one_to_one_rule.MappingMode, TestVappNat._manual)
        self.assertEqual(one_to_one_rule.ExternalIpAddress,
                         TestVappNat._ext_ip_addr)

    def test_0090_delete_nat_rule(self):
        vapp_nat = VappNat(TestVappNat._client,
                           vapp_name=TestVappNat._vapp_name,
                           network_name=TestVappNat._network_name)
        vapp_nat._get_resource()
        task = vapp_nat.delete_nat_rule(TestVappNat._rule_id)
        result = TestVappNat._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        vapp_nat._reload()
        nat_service = vapp_nat.resource.Configuration.Features.NatService
        self.assertFalse(hasattr(nat_service, 'NatRule'))

    @developerModeAware
    def test_9998_teardown(self):
        """Test the  method vdc.delete_vapp().

        Invoke the method for all the vApps created by setup.

        This test passes if all the tasks for deleting the vApps succeed.
        """
        vdc = Environment.get_test_vdc(TestVappNat._client)
        task = vdc.delete_vapp(name=TestVappNat._vapp_name, force=True)
        result = TestVappNat._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_9999_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestVappNat._client.logout()


if __name__ == '__main__':
    unittest.main()
