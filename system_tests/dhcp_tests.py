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
from pyvcloud.vcd.dhcp_pool import DhcpPool
from pyvcloud.vcd.gateway import Gateway


class TestDhcp(BaseTestCase):
    """Test DHCP functionalities implemented in pyvcloud."""
    # All tests in this module should be run as System Administrator.
    _pool_ip_range = '30.20.10.110-30.20.10.112'
    _name = GatewayConstants.name

    def test_0000_setup(self):
        """Add DHCP pool in the gateway.

        Invokes the add_dhcp_pool of the gateway.
        """
        TestDhcp._client = Environment.get_sys_admin_client()
        TestDhcp._config = Environment.get_config()
        gateway = Environment. \
            get_test_gateway(TestDhcp._client)
        gateway_obj = Gateway(TestDhcp._client,
                              TestDhcp._name,
                              href=gateway.get('href'))
        gateway_obj.add_dhcp_pool(TestDhcp._pool_ip_range)
        dhcp_resource = gateway_obj.get_dhcp()
        # Verify
        matchFound = False
        for ipPool in dhcp_resource.ipPools.ipPool:
            if ipPool.ipRange.text == TestDhcp._pool_ip_range:
                matchFound = True
                break
        self.assertTrue(matchFound)

    def test_0001_list_dhcp_pools(self):
        """List DHCP pools of the gateway.

        Invokes the list_dhcp_pools of the gateway.
        """
        TestDhcp._config = Environment.get_config()
        gateway = Environment. \
            get_test_gateway(TestDhcp._client)
        gateway_obj = Gateway(TestDhcp._client,
                              TestDhcp._name,
                              href=gateway.get('href'))
        dhcp_pool_list = gateway_obj.list_dhcp_pools()
        # Verify
        self.assertTrue(len(dhcp_pool_list) > 0)

    def test_002_get_dhcp_pool_info(self):
        """Get the details of DHCP Pool.

        Invokes the get_pool_info of the DhcpPool.
        """
        gateway = Environment. \
            get_test_gateway(TestDhcp._client)
        gateway_obj = Gateway(TestDhcp._client,
                              TestDhcp._name,
                              href=gateway.get('href'))
        dhcp_pool_list = gateway_obj.list_dhcp_pools()
        pool_id = dhcp_pool_list[0]['ID']
        pool_obj = DhcpPool(TestDhcp._client, self._name, pool_id)
        pool_info = pool_obj.get_pool_info()
        #Verify
        self.assertTrue(len(pool_info) > 0)
        self.assertEqual(pool_info['IPRange'], TestDhcp._pool_ip_range)

    def test_0098_teardown(self):
        """Remove the DHCP ip pools of gateway.
         Invokes the delete_pool of the DhcpPool.
        """
        gateway = Environment. \
            get_test_gateway(TestDhcp._client)
        gateway_obj = Gateway(TestDhcp._client,
                              TestDhcp._name,
                              href=gateway.get('href'))
        dhcp_resource = gateway_obj.get_dhcp()
        for ip_pool in dhcp_resource.ipPools.ipPool:
            dhcp_pool_object = DhcpPool(TestDhcp._client, self._name,
                                        ip_pool.poolId)
            dhcp_pool_object.delete_pool()
        dhcp_resource = gateway_obj.get_dhcp()
        self.assertFalse(hasattr(dhcp_resource.ipPools, 'ipPool'))

    def test_0099_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestDhcp._client.logout()


if __name__ == '__main__':
    unittest.main()
