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
from pyvcloud.vcd.vapp_dhcp import VappDhcp
from pyvcloud.system_test_framework.vapp_constants import VAppConstants
from pyvcloud.system_test_framework.environment import Environment
from pyvcloud.system_test_framework.environment import developerModeAware
from pyvcloud.vcd.client import TaskStatus


class TestVappDhcp(BaseTestCase):
    """Test vapp dhcp functionalities implemented in pyvcloud."""
    _vapp_name = VAppConstants.name
    _vapp_network_name = VAppConstants.network1_name
    _vapp_network_dhcp_ip_range = '90.80.70.101-90.80.70.120'
    _vapp_network_start_dhcp_ip = '90.80.70.101'
    _vapp_network_end_dhcp_ip = '90.80.70.120'
    _vapp_network_dhcp_default_lease_time = 3600
    _vapp_network_dhcp_max_lease_time = 7200
    _enable = True
    _disable = False

    def test_0000_setup(self):
        TestVappDhcp._client = Environment.get_sys_admin_client()
        vapp = Environment.get_test_vapp_with_network(TestVappDhcp._client)
        self.assertIsNotNone(vapp)

    def test_0011_set_dhcp_service(self):
        vapp_dhcp = VappDhcp(
            client=TestVappDhcp._client,
            vapp_name=TestVappDhcp._vapp_name,
            network_name=TestVappDhcp._vapp_network_name)
        task = vapp_dhcp.set_dhcp_service(
            TestVappDhcp._vapp_network_dhcp_ip_range,
            TestVappDhcp._vapp_network_dhcp_default_lease_time,
            TestVappDhcp._vapp_network_dhcp_max_lease_time)
        TestVappDhcp._client.get_task_monitor().wait_for_success(task=task)
        vapp_dhcp._reload()
        dhcp_service = vapp_dhcp.resource.Configuration.Features.DhcpService
        self.assertTrue(dhcp_service.IsEnabled)
        self.assertEqual(dhcp_service.IpRange.StartAddress,
                         TestVappDhcp._vapp_network_start_dhcp_ip)
        self.assertEqual(dhcp_service.IpRange.EndAddress,
                         TestVappDhcp._vapp_network_end_dhcp_ip)

    def test_0012_enable_dhcp_service(self):
        vapp_dhcp = VappDhcp(
            TestVappDhcp._client,
            vapp_name=TestVappDhcp._vapp_name,
            network_name=TestVappDhcp._vapp_network_name)
        task = vapp_dhcp.enable_dhcp_service(TestVappDhcp._enable)
        TestVappDhcp._client.get_task_monitor().wait_for_success(task=task)
        vapp_dhcp._reload()
        dhcp_service = vapp_dhcp.resource.Configuration.Features.DhcpService
        self.assertTrue(dhcp_service.IsEnabled)
        task = vapp_dhcp.enable_dhcp_service(TestVappDhcp._disable)
        TestVappDhcp._client.get_task_monitor().wait_for_success(task=task)
        vapp_dhcp._reload()
        dhcp_service = vapp_dhcp.resource.Configuration.Features.DhcpService
        self.assertFalse(dhcp_service.IsEnabled)

    @developerModeAware
    def test_9998_teardown(self):
        """Test the  method vdc.delete_vapp().

        Invoke the method for all the vApps created by setup.

        This test passes if all the tasks for deleting the vApps succeed.
        """
        vdc = Environment.get_test_vdc(TestVappDhcp._client)
        task = vdc.delete_vapp(name=TestVappDhcp._vapp_name, force=True)
        result = TestVappDhcp._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_9999_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestVappDhcp._client.logout()


if __name__ == '__main__':
    unittest.main()
