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
from pyvcloud.system_test_framework.environment import developerModeAware
from pyvcloud.system_test_framework.environment import Environment
from pyvcloud.system_test_framework.vapp_constants import VAppConstants
from pyvcloud.vcd.vapp_ip_allocations import VappNwAddress
from pyvcloud.vcd.client import IpAddressMode
from pyvcloud.vcd.client import NetworkAdapterType
from pyvcloud.vcd.client import TaskStatus
from pyvcloud.vcd.vm import VM


class TestVappNwAddress(BaseTestCase):
    """Test vapp IP allocation functionalities implemented in pyvcloud."""
    _vapp_name = VAppConstants.name
    _vapp_network_name = VAppConstants.network1_name
    _vm_name = VAppConstants.vm1_name
    _ip_address = '90.80.70.10'

    def test_0000_setup(self):
        TestVappNwAddress._client = Environment.get_sys_admin_client()
        vapp = Environment.get_test_vapp_with_network(
            TestVappNwAddress._client)
        self.assertIsNotNone(vapp)
        vm_resource = vapp.get_vm(TestVappNwAddress._vm_name)
        TestVappNwAddress._vm_href = vm_resource.get('href')
        vm = VM(TestVappNwAddress._client, href=TestVappNwAddress._vm_href)
        task = vm.add_nic(NetworkAdapterType.E1000.value, True, True,
                          TestVappNwAddress._vapp_network_name,
                          IpAddressMode.MANUAL.value,
                          TestVappNwAddress._ip_address)
        result = TestVappNwAddress._client.get_task_monitor().wait_for_success(
            task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0011_list_ip_allocations(self):
        vapp_nw_address = VappNwAddress(
            client=TestVappNwAddress._client,
            vapp_name=TestVappNwAddress._vapp_name,
            network_name=TestVappNwAddress._vapp_network_name)
        list_ip_address = vapp_nw_address.list_ip_allocations()
        self.assertTrue(len(list_ip_address) > 0)

    @developerModeAware
    def test_9998_teardown(self):
        """Test the  method vdc.delete_vapp().

        Invoke the method for all the vApps created by setup.

        This test passes if all the tasks for deleting the vApps succeed.
        """
        vdc = Environment.get_test_vdc(TestVappNwAddress._client)
        task = vdc.delete_vapp(name=TestVappNwAddress._vapp_name, force=True)
        result = TestVappNwAddress._client.get_task_monitor().wait_for_success(
            task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_9999_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestVappNwAddress._client.logout()


if __name__ == '__main__':
    unittest.main()
