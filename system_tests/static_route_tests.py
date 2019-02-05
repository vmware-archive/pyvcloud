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
from pyvcloud.vcd.static_route import StaticRoute


class TestStaticRoute(BaseTestCase):
    """Test Static Route functionalities implemented in pyvcloud."""
    # All tests in this module should be run as System Administrator.
    _next_hop = '2.2.3.80'
    _network = '192.169.1.0/24'
    _name = GatewayConstants.name
    _network_id = None
    _new_next_hop = '2.2.3.82'
    _new_mtu = 1800
    _new_desc = 'Static Route edited'

    def test_0000_setup(self):
        """Add Static Route in the gateway.

        Invokes the add_static_route of the gateway.
        """
        TestStaticRoute._client = Environment.get_sys_admin_client()
        TestStaticRoute._config = Environment.get_config()
        gateway = Environment. \
            get_test_gateway(TestStaticRoute._client)
        gateway_obj = Gateway(TestStaticRoute._client,
                              TestStaticRoute._name,
                              href=gateway.get('href'))
        gateway_obj.add_static_route(TestStaticRoute._network,
                                     TestStaticRoute._next_hop)
        static_route = gateway_obj.get_static_routes()
        #Verify
        match_found = False
        for route in static_route.staticRoutes.route:
            if route.nextHop == TestStaticRoute._next_hop and \
               route.network == TestStaticRoute._network:
                TestStaticRoute._network_id = route.network
                match_found = True
                break
        self.assertTrue(match_found)

    def test_0001_list_static_routes(self):
        """List Static Routes of the gateway.

        Invokes the list_static_routes of the gateway.
        """
        TestStaticRoute._config = Environment.get_config()
        gateway = Environment. \
            get_test_gateway(TestStaticRoute._client)
        gateway_obj = Gateway(TestStaticRoute._client,
                              TestStaticRoute._name,
                              href=gateway.get('href'))
        static_route_list = gateway_obj.list_static_routes()
        # Verify
        self.assertTrue(len(static_route_list) > 0)

    def test_0030_update_static_routes(self):
        """Update a static route.

        Invokes the update_static_route of the StaticRoute.
        """
        static_object = StaticRoute(
            TestStaticRoute._client,
            TestStaticRoute._name,
            TestStaticRoute._network_id)
        static_object.update_static_route(
            next_hop=TestStaticRoute._new_next_hop,
            mtu=TestStaticRoute._new_mtu,
            description=TestStaticRoute._new_desc)

        gateway = Environment. \
            get_test_gateway(TestStaticRoute._client)
        gateway_obj = Gateway(TestStaticRoute._client,
                              TestStaticRoute._name,
                              href=gateway.get('href'))
        static_route = gateway_obj.get_static_routes()
        # Verify
        match_found = False
        for route in static_route.staticRoutes.route:
            if route.nextHop == TestStaticRoute._new_next_hop and \
               route.mtu == TestStaticRoute._new_mtu and \
               route.description == TestStaticRoute._new_desc:
                match_found = True
                break
        self.assertTrue(match_found)

    def test_0098_teardown(self):
        """Remove the static route from the gateway.

        Invokes the delete_static_route of the StaticRoute.
        """
        static_object = StaticRoute(
            TestStaticRoute._client,
            TestStaticRoute._name,
            TestStaticRoute._network_id)
        static_object.delete_static_route()
        # Verify
        gateway = Environment. \
            get_test_gateway(TestStaticRoute._client)
        gateway_obj = Gateway(TestStaticRoute._client,
                              TestStaticRoute._name,
                              href=gateway.get('href'))
        static_route = gateway_obj.get_static_routes()
        self.assertFalse(hasattr(static_route.staticRoutes, 'route'))

    def test_0099_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestStaticRoute._client.logout()


if __name__ == '__main__':
    unittest.main()
