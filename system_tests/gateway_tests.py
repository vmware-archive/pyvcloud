# VMware vCloud Director Python SDK
# Copyright (c) 2018 VMware, Inc. All Rights Reserved.
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
from pyvcloud.vcd.client import GatewayBackingConfigType
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import TaskStatus
from pyvcloud.system_test_framework.base_test import BaseTestCase
from pyvcloud.system_test_framework.environment import Environment
from pyvcloud.vcd.gateway import Gateway
from pyvcloud.vcd.platform import Platform


class TestGateway(BaseTestCase):
    """Test Gateway functionalities implemented in pyvcloud."""

    # All tests in this module should be run as System Administrator.

    _client = None
    _name = ("test_gateway1" + str(uuid1()))[:34]

    _description = "test_gateway1 description"
    _gateway = None

    def test_0000_setup(self):
        """Setup the gateway required for the other tests in this module.

        Create a gateway as per the configuration stated
        above.

        This test passes if the gateway is created successfully.
        """
        TestGateway._client = Environment.get_sys_admin_client()
        vdc = Environment.get_test_vdc(TestGateway._client)
        platform = Platform(TestGateway._client)
        external_networks = platform.list_external_networks()
        self.assertTrue(len(external_networks) > 0)
        external_network = external_networks[0]

        ext_net_resource = TestGateway._client.get_resource(
            external_network.get('href'))
        ip_scopes = ext_net_resource.xpath(
            'vcloud:Configuration/vcloud:IpScopes/vcloud:IpScope',
            namespaces=NSMAP)
        first_ipscope = ip_scopes[0]
        gateway_ip = first_ipscope.Gateway.text

        subnet_addr = gateway_ip + '/' + str(first_ipscope.SubnetPrefixLength)
        ext_net_to_participated_subnet_with_ip_settings = {
            ext_net_resource.get('name'): {
                subnet_addr: 'Auto'
            }
        }

        gateway_ip_arr = gateway_ip.split('.')
        last_ip_digit = int(gateway_ip_arr[-1]) + 1
        gateway_ip_arr[-1] = str(last_ip_digit)
        next_ip = '.'.join(gateway_ip_arr)
        ext_net_to_subnet_with_ip_range = {
            ext_net_resource.get('name'): {
                subnet_addr: [next_ip + '-' + next_ip]
            }
        }
        ext_net_to_rate_limit = {ext_net_resource.get('name'): {100: 100}}
        TestGateway._gateway = vdc.create_gateway(
            self._name, [ext_net_resource.get('name')], 'compact', None, True,
            ext_net_resource.get('name'), gateway_ip, True, False, False,
            False, True, ext_net_to_participated_subnet_with_ip_settings, True,
            ext_net_to_subnet_with_ip_range, ext_net_to_rate_limit)
        result = TestGateway._client.get_task_monitor().wait_for_success(
            task=TestGateway._gateway.Tasks.Task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0001_convert_to_advanced(self):
        """Convert the legacy gateway to advance gateway.

        Invoke the convert_to_advanced method for gateway.
        """
        gateway_obj = Gateway(TestGateway._client, self._name,
                              TestGateway._gateway.get('href'))
        task = gateway_obj.convert_to_advanced()
        result = TestGateway._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0002_enable_dr(self):
        """Enable the Distributed routing.

        Invoke the enable_distributed_routing method for the gateway.
        """
        gateway_obj = Gateway(TestGateway._client, self._name,
                              TestGateway._gateway.get('href'))
        task = gateway_obj.enable_distributed_routing(True)
        result = TestGateway._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0003_modify_form_factor(self):
        """Modify form factor.

        Invoke the modify_form_factor method for the gateway.
        """
        gateway_obj = Gateway(TestGateway._client, self._name,
                              TestGateway._gateway.get('href'))
        task = gateway_obj.modify_form_factor(
            GatewayBackingConfigType.FULL.value)
        result = TestGateway._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0004_list_external_network_ip_allocations(self):
        """List external network ip allocations.

        Invoke the list_external_network_ip_allocations of the gateway.
        """
        gateway_obj = Gateway(TestGateway._client, self._name,
                              TestGateway._gateway.get('href'))
        ip_allocations = gateway_obj.list_external_network_ip_allocations()
        self.assertTrue(bool(ip_allocations))

    def test_0098_teardown(self):
        """Test the method System.delete_gateway().

        Invoke the method for the gateway created by setup.

        This test passes if no errors are generated while deleting the gateway.
        """
        vdc = Environment.get_test_vdc(TestGateway._client)
        task = vdc.delete_gateway(TestGateway._name)
        result = TestGateway._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0099_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestGateway._client.logout()


if __name__ == '__main__':
    unittest.main()
