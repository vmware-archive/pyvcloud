# VMware vCloud Director Python SDK
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
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
from pyvcloud.vcd.client import ApiVersion
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import TaskStatus
from pyvcloud.system_test_framework.base_test import BaseTestCase
from pyvcloud.system_test_framework.environment import CommonRoles
from pyvcloud.system_test_framework.environment import Environment
from pyvcloud.system_test_framework.constants.gateway_constants import \
    GatewayConstants
from pyvcloud.vcd.nat_rule import NatRule
from pyvcloud.vcd.gateway import Gateway
from pyvcloud.vcd.utils import netmask_to_cidr_prefix_len


class TestNatRule(BaseTestCase):
    """Test Nat Rule functionalities implemented in pyvcloud."""
    # All tests in this module should be run as System Administrator.
    _client = None
    _name = (GatewayConstants.name + str(uuid1()))[:34]
    _description = GatewayConstants.description + str(uuid1())
    _gateway = None
    _snat_action = 'snat'
    _snat_orig_addr = '2.2.3.7'
    _snat_trans_addr = '2.2.3.8'
    _dnat_action = 'dnat'
    _dnat1_orig_addr = '2.2.3.10'
    _dnat1_trans_addr = '2.2.3.11-2.2.3.12'
    _dnat1_protocol = 'tcp'
    _dnat1_orig_port = 80
    _dnat1_trans_port = 80
    _dnat2_orig_addr = '2.2.3.15'
    _dnat2_trans_addr = '2.2.3.16-2.2.3.17'
    _dnat2_protocol = 'icmp'
    _dnat2_desc = 'icmp protocol'

    def test_0000_setup(self):
        """Setup the gateway required for the other tests in this module.

        Create a gateway as per the configuration stated
        above.

        This test passes if the gateway is created successfully.
        """
        TestNatRule._client = Environment.get_sys_admin_client()
        TestNatRule._vdc = Environment.get_test_vdc(TestNatRule._client)

        TestNatRule._org_client = Environment.get_client_in_default_org(
            CommonRoles.ORGANIZATION_ADMINISTRATOR)
        TestNatRule._config = Environment.get_config()
        TestNatRule._api_version = TestNatRule._config['vcd']['api_version']

        external_network = Environment.get_test_external_network(
            TestNatRule._client)

        ext_net_resource = external_network.get_resource()
        ip_scopes = ext_net_resource.xpath(
            'vcloud:Configuration/vcloud:IpScopes/vcloud:IpScope',
            namespaces=NSMAP)
        first_ipscope = ip_scopes[0]
        gateway_ip = first_ipscope.Gateway.text
        prefix_len = netmask_to_cidr_prefix_len(gateway_ip,
                                           first_ipscope.Netmask.text)
        subnet_addr = gateway_ip + '/' + str(prefix_len)
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
        if float(TestNatRule._api_version) <= float(
                ApiVersion.VERSION_30.value):
            TestNatRule._gateway = \
                TestNatRule._vdc.create_gateway_api_version_30(
                    self._name, [ext_net_resource.get('name')], 'compact',
                    None,
                    True, ext_net_resource.get('name'), gateway_ip, True,
                    False,
                    False, False, True,
                    ext_net_to_participated_subnet_with_ip_settings, True,
                    ext_net_to_subnet_with_ip_range, ext_net_to_rate_limit)
        else:
            TestNatRule._gateway = TestNatRule._vdc.create_gateway(
                self._name, [ext_net_resource.get('name')], 'compact', None,
                True, ext_net_resource.get('name'), gateway_ip, True, False,
                False, False, True,
                ext_net_to_participated_subnet_with_ip_settings, True,
                ext_net_to_subnet_with_ip_range, ext_net_to_rate_limit)

        result = TestNatRule._client.get_task_monitor().wait_for_success(
            task=TestNatRule._gateway.Tasks.Task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def __get_subnet_participation(self, gateway, ext_network):
        for gatewayinf in \
                gateway.Configuration.GatewayInterfaces.GatewayInterface:
            if gatewayinf.Name == ext_network:
                return gatewayinf.SubnetParticipation

    def __validate_ip_range(self, IpRanges, _ip_range1):
        """ Validate if the ip range present in the existing ip ranges """
        _ip_ranges = _ip_range1.split('-')
        _ip_range1_start_address = _ip_ranges[0]
        _ip_range1_end_address = _ip_ranges[1]
        for ip_range in IpRanges.IpRange:
            if ip_range.StartAddress == _ip_range1_start_address:
                self.assertEqual(ip_range.EndAddress, _ip_range1_end_address)

    def test_0001_convert_to_advanced(self):
        """Convert the legacy gateway to advance gateway.
        Invoke the convert_to_advanced method for gateway.
        """
        if float(TestNatRule._api_version) >= float(
                ApiVersion.VERSION_32.value):
            return
        gateway_obj = Gateway(TestNatRule._org_client, self._name,
                              TestNatRule._gateway.get('href'))
        task = gateway_obj.convert_to_advanced()
        result = TestNatRule._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0005_add_sub_allocated_ip_pools(self):
        """It adds the sub allocated ip pools to gateway.

        Invokes the add_sub_allocated_ip_pools of the gateway.
        """
        gateway_obj = Gateway(TestNatRule._client, self._name,
                              TestNatRule._gateway.get('href'))
        ip_allocations = gateway_obj.list_configure_ip_settings()
        ip_allocation = ip_allocations[0]
        ext_network = ip_allocation.get('external_network')
        config = TestNatRule._config['external_network']
        gateway_sub_allocated_ip_range = \
            config['gateway_sub_allocated_ip_range']
        ip_range_list = [gateway_sub_allocated_ip_range]

        task = gateway_obj.add_sub_allocated_ip_pools(ext_network,
                                                      ip_range_list)
        result = TestNatRule._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        gateway_obj = Gateway(TestNatRule._client, self._name,
                              TestNatRule._gateway.get('href'))
        subnet_participation = self.__get_subnet_participation(
            gateway_obj.get_resource(), ext_network)
        ip_ranges = gateway_obj.get_sub_allocate_ip_ranges_element(
            subnet_participation)
        self.__validate_ip_range(ip_ranges, gateway_sub_allocated_ip_range)

    def test_0010_add_nat_rule(self):
        """Add Nat Rule's in the gateway."""

        gateway_obj = Gateway(TestNatRule._client, self._name,
                              TestNatRule._gateway.get('href'))
        # Create SNAT Rule
        gateway_obj.add_nat_rule(
            action=TestNatRule._snat_action,
            original_address=TestNatRule._snat_orig_addr,
            translated_address=TestNatRule._snat_trans_addr)
        # Create DNAT Rule for tcp/udp protocol
        gateway_obj.add_nat_rule(
            action=TestNatRule._dnat_action,
            original_address=TestNatRule._dnat1_orig_addr,
            translated_address=TestNatRule._dnat1_trans_addr,
            protocol=TestNatRule._dnat1_protocol,
            original_port=TestNatRule._dnat1_orig_port,
            translated_port=TestNatRule._dnat1_trans_port)
        # Create DNAT Rule for icmp protocol
        gateway_obj.add_nat_rule(
            action=TestNatRule._dnat_action,
            original_address=TestNatRule._dnat2_orig_addr,
            translated_address=TestNatRule._dnat2_trans_addr,
            description=TestNatRule._dnat2_protocol,
            protocol=TestNatRule._dnat2_protocol)
        nat_rule = gateway_obj.get_nat_rules()
        #Verify
        snat_count = 0
        dnat_count = 0
        for natRule in nat_rule.natRules.natRule:
            if natRule.action == 'snat':
                snat_count += 1
            if natRule.action == 'dnat':
                dnat_count += 1
        self.assertTrue(snat_count == 1)
        self.assertTrue(dnat_count == 2)

    def test_0098_teardown(self):
        """Test method to delete a nat rule and gateway.

        Invoke the method for the gateway created by setup.

        This test passes if no errors are generated while deleting the gateway.
        """
        gateway_obj = Gateway(TestNatRule._client, self._name,
                              TestNatRule._gateway.get('href'))
        nat_rule = gateway_obj.get_nat_rules()
        for natRule in nat_rule.natRules.natRule:
            rule_id = natRule.ruleId
            break
        nat_obj = NatRule(TestNatRule._client, self._name, rule_id)
        # deleting single nat rule as gateway deletion will clear all
        nat_obj.delete_nat_rule()

        vdc = Environment.get_test_vdc(TestNatRule._client)
        task = vdc.delete_gateway(TestNatRule._name)
        result = TestNatRule._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0099_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestNatRule._client.logout()


if __name__ == '__main__':
    unittest.main()
