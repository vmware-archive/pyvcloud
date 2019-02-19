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
from pyvcloud.vcd.dhcp_binding import DhcpBinding
from pyvcloud.vcd.gateway import Gateway


class TestDhcpBinding(BaseTestCase):
    """Test DHCP functionalities implemented in pyvcloud."""
    # All tests in this module should be run as System Administrator.
    _name = GatewayConstants.name
    _mac_address = '00:14:22:01:23:45'
    _host_name = 'xyzName'
    _binding_ip_address = '10.20.30.41'

    def test_0000_setup(self):
        """Add DHCP binding in the gateway.

        Invokes the add_dhcp_binding of the gateway.
        """
        TestDhcpBinding._client = Environment.get_sys_admin_client()
        TestDhcpBinding._config = Environment.get_config()
        gateway = Environment. \
            get_test_gateway(TestDhcpBinding._client)
        gateway_obj = Gateway(TestDhcpBinding._client,
                              TestDhcpBinding._name,
                              href=gateway.get('href'))
        gateway_obj.add_dhcp_binding(TestDhcpBinding._mac_address,
                                     TestDhcpBinding._host_name,
                                     TestDhcpBinding._binding_ip_address)
        dhcp_resource = gateway_obj.get_dhcp()
        # Verify
        matchFound = False
        for static_binding in dhcp_resource.staticBindings.staticBinding:
            if static_binding.hostname.text == TestDhcpBinding._host_name:
                matchFound = True
                break
        self.assertTrue(matchFound)

    def test_0001_list_dhcp_bindings(self):
        """List DHCP binding of the gateway.

        Invokes the list_dhcp_binding of the gateway.
        """
        TestDhcpBinding._config = Environment.get_config()
        gateway = Environment. \
            get_test_gateway(TestDhcpBinding._client)
        gateway_obj = Gateway(TestDhcpBinding._client,
                              TestDhcpBinding._name,
                              href=gateway.get('href'))
        dhcp_binding_list = gateway_obj.list_dhcp_binding()
        # Verify
        self.assertTrue(len(dhcp_binding_list) > 0)

    def test_0098_teardown(self):
        """Remove the DHCP bindings of gateway.

         Invokes the delete_binding of the DhcpBinding.
        """
        gateway = Environment. \
            get_test_gateway(TestDhcpBinding._client)
        gateway_obj = Gateway(TestDhcpBinding._client,
                              TestDhcpBinding._name,
                              href=gateway.get('href'))
        dhcp_resource = gateway_obj.get_dhcp()
        for static_binding in dhcp_resource.staticBindings.staticBinding:
            dhcp_binding_object = DhcpBinding(TestDhcpBinding._client,
                                              gateway_name=
                                              TestDhcpBinding._name,
                                              binding_id=
                                              static_binding.bindingId)
            dhcp_binding_object.delete_binding()
        dhcp_resource = gateway_obj.get_dhcp()
        self.assertFalse(hasattr(dhcp_resource.staticBindings,
                                 'staticBinding'))

    def test_0099_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestDhcpBinding._client.logout()


if __name__ == '__main__':
    unittest.main()
