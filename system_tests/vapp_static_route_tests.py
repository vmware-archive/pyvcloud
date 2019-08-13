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
from pyvcloud.vcd.vapp_static_route import VappStaticRoute
from pyvcloud.system_test_framework.vapp_constants import VAppConstants
from pyvcloud.system_test_framework.environment import Environment
from pyvcloud.system_test_framework.environment import developerModeAware
from pyvcloud.vcd.client import TaskStatus


class TestVappStaticRoute(BaseTestCase):
    """Test vapp static route functionalities implemented in pyvcloud."""
    _vapp_name = VAppConstants.name
    _network_name = VAppConstants.network1_name
    _org_vdc_network_name = 'test-direct-vdc-network'
    _enable = True
    _disable = False
    _route_name = 'test_route'
    _network_cidr = '2.2.3.0/24'
    _next_hop_ip = '2.2.3.4'

    _update_route_name = 'update_test_route'
    _update_next_hop_ip = '2.2.3.10'

    def test_0000_setup(self):
        TestVappStaticRoute._client = Environment.get_sys_admin_client()
        vapp = Environment.get_test_vapp_with_network(
            TestVappStaticRoute._client)
        vapp.reload()
        task = vapp.connect_vapp_network_to_ovdc_network(
            network_name=TestVappStaticRoute._network_name,
            orgvdc_network_name=TestVappStaticRoute._org_vdc_network_name)
        result = TestVappStaticRoute._client.get_task_monitor(
        ).wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0010_enable_service(self):
        vapp_route = VappStaticRoute(
            TestVappStaticRoute._client,
            vapp_name=TestVappStaticRoute._vapp_name,
            network_name=TestVappStaticRoute._network_name)
        # disable NAT service
        task = vapp_route.enable_service(TestVappStaticRoute._disable)
        result = TestVappStaticRoute._client.get_task_monitor(
        ).wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        vapp_route._reload()
        features = vapp_route.resource.Configuration.Features
        self.assertFalse(features.StaticRoutingService.IsEnabled)
        # enable NAT service
        task = vapp_route.enable_service(TestVappStaticRoute._enable)
        result = TestVappStaticRoute._client.get_task_monitor(
        ).wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        vapp_route._reload()
        features = vapp_route.resource.Configuration.Features
        self.assertTrue(features.StaticRoutingService.IsEnabled)

    def test_0020_add(self):
        vapp_route = VappStaticRoute(
            TestVappStaticRoute._client,
            vapp_name=TestVappStaticRoute._vapp_name,
            network_name=TestVappStaticRoute._network_name)
        task = vapp_route.add(TestVappStaticRoute._route_name,
                              TestVappStaticRoute._network_cidr,
                              TestVappStaticRoute._next_hop_ip)
        result = TestVappStaticRoute._client.get_task_monitor(
        ).wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        vapp_route._reload()
        features = vapp_route.resource.Configuration.Features
        self.assertTrue(hasattr(features.StaticRoutingService, 'StaticRoute'))

    def test_0030_list(self):
        vapp_route = VappStaticRoute(
            TestVappStaticRoute._client,
            vapp_name=TestVappStaticRoute._vapp_name,
            network_name=TestVappStaticRoute._network_name)
        result = vapp_route.list()
        self.assertEqual(result[0]['Name'], TestVappStaticRoute._route_name)

    def test_0040_update(self):
        vapp_route = VappStaticRoute(
            TestVappStaticRoute._client,
            vapp_name=TestVappStaticRoute._vapp_name,
            network_name=TestVappStaticRoute._network_name)
        task = vapp_route.update(
            name=TestVappStaticRoute._route_name,
            new_name=TestVappStaticRoute._update_route_name,
            next_hop_ip=TestVappStaticRoute._update_next_hop_ip)
        result = TestVappStaticRoute._client.get_task_monitor(
        ).wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        vapp_route._reload()
        result = vapp_route.list()
        self.assertEqual(result[0]['Name'],
                         TestVappStaticRoute._update_route_name)
        self.assertEqual(result[0]['Next Hop IP'],
                         TestVappStaticRoute._update_next_hop_ip)

        #revert back changes
        task = vapp_route.update(name=TestVappStaticRoute._update_route_name,
                                 new_name=TestVappStaticRoute._route_name,
                                 next_hop_ip=TestVappStaticRoute._next_hop_ip)
        result = TestVappStaticRoute._client.get_task_monitor(
        ).wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        vapp_route._reload()
        result = vapp_route.list()
        self.assertEqual(result[0]['Name'], TestVappStaticRoute._route_name)
        self.assertEqual(result[0]['Next Hop IP'],
                         TestVappStaticRoute._next_hop_ip)

    def test_0090_delete(self):
        vapp_route = VappStaticRoute(
            TestVappStaticRoute._client,
            vapp_name=TestVappStaticRoute._vapp_name,
            network_name=TestVappStaticRoute._network_name)
        task = vapp_route.delete(TestVappStaticRoute._route_name)
        result = TestVappStaticRoute._client.get_task_monitor(
        ).wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        vapp_route._reload()
        features = vapp_route.resource.Configuration.Features
        self.assertFalse(hasattr(features.StaticRoutingService, 'StaticRoute'))

    @developerModeAware
    def test_9998_teardown(self):
        """Test the  method vdc.delete_vapp().

        Invoke the method for all the vApps created by setup.

        This test passes if all the tasks for deleting the vApps succeed.
        """
        vdc = Environment.get_test_vdc(TestVappStaticRoute._client)
        task = vdc.delete_vapp(name=TestVappStaticRoute._vapp_name, force=True)
        result = TestVappStaticRoute._client.get_task_monitor(
        ).wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_9999_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestVappStaticRoute._client.logout()


if __name__ == '__main__':
    unittest.main()
