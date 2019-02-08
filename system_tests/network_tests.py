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

from uuid import uuid1

from pyvcloud.system_test_framework.base_test import BaseTestCase
from pyvcloud.system_test_framework.environment import CommonRoles
from pyvcloud.system_test_framework.environment import developerModeAware
from pyvcloud.system_test_framework.environment import Environment
from pyvcloud.system_test_framework.constants.gateway_constants import \
    GatewayConstants

from pyvcloud.vcd.client import TaskStatus
from pyvcloud.vcd.exceptions import AccessForbiddenException
from pyvcloud.vcd.exceptions import EntityNotFoundException
from pyvcloud.vcd.gateway import Gateway
from pyvcloud.vcd.vdc_network import VdcNetwork


class TestNetwork(BaseTestCase):
    """Test network functionalities implemented in pyvcloud."""

    # Once pyvcloud is mature enough to handle external networks, directly
    # connected/routed org vdc networks, vApp networks. We will add more tests.

    _test_runner_role = CommonRoles.ORGANIZATION_ADMINISTRATOR
    _client = None
    _system_client = None
    _vapp_author_client = None

    _isolated_orgvdc_network_name = 'isolated_orgvdc_network_' + str(uuid1())
    _isolated_orgvdc_network_gateway_ip = '10.0.0.1/24'

    _routed_orgvdc_network_gateway_ip = '6.6.2.1/10'
    _ip_range = '6.6.2.2-6.6.2.10'
    _new_ip_range = '6.6.2.20-6.6.2.30'

    _non_existent_isolated_orgvdc_network_name = 'non_existent_isolated_' + \
        'orgvdc_network_' + str(uuid1())

    _routed_org_vdc_network_name = 'routed_orgvdc_network_' + str(uuid1())
    _routed_org_vdc_network_new_name = 'routed_orgvdc_network_new_' + str(
        uuid1())
    _dns1 = '8.8.8.8'
    _dns2 = '8.8.8.9'
    _dns_suffix = 'example.com'

    def test_0000_setup(self):
        """Setup the networks required for the other tests in this module.

        Create an isolated org vdc network as per the configuration stated
        above.

        This test passes if the isolated orgvdc network is created
        successfully.
        """
        logger = Environment.get_default_logger()
        TestNetwork._client = Environment.get_client_in_default_org(
            TestNetwork._test_runner_role)
        TestNetwork._system_client = Environment.get_sys_admin_client()
        TestNetwork._vapp_author_client = \
            Environment.get_client_in_default_org(CommonRoles.VAPP_AUTHOR)
        vdc = Environment.get_test_vdc(TestNetwork._client)

        logger.debug('Creating isolated orgvdc network : ' +
                     TestNetwork._isolated_orgvdc_network_name)
        result = vdc.create_isolated_vdc_network(
            network_name=TestNetwork._isolated_orgvdc_network_name,
            network_cidr=TestNetwork._isolated_orgvdc_network_gateway_ip)
        TestNetwork._client.get_task_monitor().wait_for_success(
            task=result.Tasks.Task[0])

    def test_0005_create_routed_orgvdc_network(self):
        """Test creation of routed vdc network.

        Fetches the gateway and invoke VDC.create_gateway method.
        """
        vdc = Environment.get_test_vdc(TestNetwork._client)
        result = vdc.create_routed_vdc_network(
            network_name=TestNetwork._routed_org_vdc_network_name,
            gateway_name=GatewayConstants.name,
            network_cidr=TestNetwork._routed_orgvdc_network_gateway_ip,
            description='Dummy description')
        task = TestNetwork._client.get_task_monitor().wait_for_success(
            task=result.Tasks.Task[0])
        assert task.get('status') == TaskStatus.SUCCESS.value

    def test_0010_list_isolated_orgvdc_networks(self):
        """Test the method vdc.list_orgvdc_isolated_networks().

        Fetches all isolated orgvdc networks in the current organization.

        This test passes if the network created during setup is present in the
        retrieved list of networks.
        """
        vdc = Environment.get_test_vdc(TestNetwork._client)
        networks = vdc.list_orgvdc_isolated_networks()
        for network in networks:
            if network.get('name') == \
               TestNetwork._isolated_orgvdc_network_name:
                return

        self.fail('Retrieved list of isolated orgvdc network doesn\'t'
                  'contain ' + TestNetwork._isolated_orgvdc_network_name)

    def test_0020_get_isolated_orgvdc_network(self):
        """Test the method vdc.get_isolated_orgvdc_network().

        Retrieve the isolated orgvdc network created during setup.

        This test passes if the network created during setup is retrieved
        successfully without any errors.
        """
        vdc = Environment.get_test_vdc(TestNetwork._client)
        network = vdc.get_isolated_orgvdc_network(
            TestNetwork._isolated_orgvdc_network_name)
        self.assertEqual(TestNetwork._isolated_orgvdc_network_name,
                         network.get('name'))

    def test_0030_get_non_existent_isolated_orgvdc_network(self):
        """Test the method vdc.get_isolated_orgvdc_network().

        This test passes if the network retrieval operation fails with a
        EntityNotFoundException.
        """
        vdc = Environment.get_test_vdc(TestNetwork._client)
        try:
            vdc.get_isolated_orgvdc_network(
                TestNetwork._non_existent_isolated_orgvdc_network_name)
            self.fail('Should not be able to fetch isolated orgvdc network ' +
                      TestNetwork._non_existent_isolated_orgvdc_network_name)
        except EntityNotFoundException as e:
            return

    def test_0035_list_routed_orgvdc_networks(self):
        vdc = Environment.get_test_vdc(TestNetwork._client)
        result = vdc.list_orgvdc_routed_networks()
        assert len(result) > 0

    def test_0040_list_isolated_orgvdc_networks_as_non_admin_user(self):
        """Test the method vdc.list_orgvdc_isolated_networks().

        Tries to fetches all isolated orgvdc networks in the current
        organization as a non admin user.

        This test passes if the operation fails with an
        AccessForbiddenException.
        """
        vdc = Environment.get_test_vdc(TestNetwork._vapp_author_client)
        try:
            result = vdc.list_orgvdc_isolated_networks()
            if len(result) > 0:
                self.fail('Should not have been able to list isolated orgvdc'
                          'networks as non admin user.')
        except AccessForbiddenException as e:
            return

    def test_0050_get_isolated_orgvdc_network_as_non_admin_user(self):
        """Test the method vdc.get_isolated_orgvdc_network().

        Tries to retrieve the isolated orgvdc network created during setup as a
        non admin user.

        This test passes if the operation fails with an
        AccessForbiddenException.
        """
        vdc = Environment.get_test_vdc(TestNetwork._vapp_author_client)
        try:
            vdc.get_isolated_orgvdc_network(
                TestNetwork._isolated_orgvdc_network_name)
            self.fail('Should not be able to fetch isolated orgvdc network ' +
                      TestNetwork._isolated_orgvdc_network_name + ' as a non' +
                      'admin user.')
        except AccessForbiddenException as e:
            return

    def test_0060_list_orgvdc_network_records_as_non_admin_user(self):
        """Test the method vdc.list_orgvdc_network_records().

        This test passes if the record of the network created during setup is
        present in the retrieved list of networks.
        """
        vdc = Environment.get_test_vdc(TestNetwork._vapp_author_client)
        records_dict = vdc.list_orgvdc_network_records()
        for net_name in records_dict.keys():
            if net_name == TestNetwork._isolated_orgvdc_network_name:
                return

        self.fail('Retrieved list of orgvdc network records doesn\'t ' +
                  'contain ' + TestNetwork._isolated_orgvdc_network_name)

    def test_0070_get_orgvdc_network_admin_href_as_non_admin_user(self):
        """Test the method vdc.get_orgvdc_network_admin_href_by_name().

        This test passes if the href of the network created during setup is
        retrieved successfully without any errors.
        """
        vdc = Environment.get_test_vdc(TestNetwork._vapp_author_client)
        href = vdc.get_orgvdc_network_admin_href_by_name(
            TestNetwork._isolated_orgvdc_network_name)
        self.assertIsNotNone(href)

    def test_0075_edit_name_description_and_shared_state_for_routed_network(
            self):
        vdc = Environment.get_test_vdc(TestNetwork._client)
        org_vdc_routed_nw = vdc.get_routed_orgvdc_network(
            TestNetwork._routed_org_vdc_network_name)
        vdcNetwork = VdcNetwork(
            TestNetwork._client, resource=org_vdc_routed_nw)
        result = vdcNetwork.edit_name_description_and_shared_state(
            TestNetwork._routed_org_vdc_network_new_name, 'Test '
            'Description', True)

        task = TestNetwork._client.get_task_monitor().wait_for_success(
            task=result)
        self.assertEqual(task.get('status'), TaskStatus.SUCCESS.value)
        # Resetting to original name
        result = vdcNetwork.edit_name_description_and_shared_state(
            TestNetwork._routed_org_vdc_network_name, None, False)

        task = TestNetwork._client.get_task_monitor().wait_for_success(
            task=result)
        self.assertEqual(task.get('status'), TaskStatus.SUCCESS.value)

    def test_0076_add_static_ip_pool(self):
        vdc = Environment.get_test_vdc(TestNetwork._client)
        org_vdc_routed_nw = vdc.get_routed_orgvdc_network(
            TestNetwork._routed_org_vdc_network_name)
        vdcNetwork = VdcNetwork(
            TestNetwork._client, resource=org_vdc_routed_nw)
        result = vdcNetwork.add_static_ip_pool_and_dns(
            [TestNetwork._ip_range], TestNetwork._dns1, TestNetwork._dns2,
            TestNetwork._dns_suffix)

        task = TestNetwork._client.get_task_monitor().wait_for_success(
            task=result)
        self.assertEqual(task.get('status'), TaskStatus.SUCCESS.value)

        result = vdcNetwork.add_static_ip_pool_and_dns(None, TestNetwork._dns1,
                                                       TestNetwork._dns2,
                                                       TestNetwork._dns_suffix)
        task = TestNetwork._client.get_task_monitor().wait_for_success(
            task=result)
        self.assertEqual(task.get('status'), TaskStatus.SUCCESS.value)

        result = vdcNetwork.add_static_ip_pool_and_dns(None, TestNetwork._dns1)
        task = TestNetwork._client.get_task_monitor().wait_for_success(
            task=result)
        self.assertEqual(task.get('status'), TaskStatus.SUCCESS.value)

        result = vdcNetwork.add_static_ip_pool_and_dns(None, None, None,
                                                       TestNetwork._dns_suffix)
        task = TestNetwork._client.get_task_monitor().wait_for_success(
            task=result)
        self.assertEqual(task.get('status'), TaskStatus.SUCCESS.value)
        # Verify
        vdcNetwork.reload()
        vdc_routed_nw = vdcNetwork.get_resource()
        ip_scope = vdc_routed_nw.Configuration.IpScopes.IpScope
        ip_ranges = ip_scope.IpRanges.IpRange
        match_found = False
        for ip_range in ip_ranges:
            if (ip_range.StartAddress + '-' + ip_range.EndAddress) == \
                    TestNetwork._ip_range:
                match_found = True
        self.assertTrue(match_found)
        self.assertTrue(ip_scope.Dns1, TestNetwork._dns1)
        self.assertTrue(ip_scope.Dns2, TestNetwork._dns2)
        self.assertTrue(ip_scope.DnsSuffix, TestNetwork._dns_suffix)

    def test_0077_modify_static_ip_pool(self):
        vdc = Environment.get_test_vdc(TestNetwork._client)
        org_vdc_routed_nw = vdc.get_routed_orgvdc_network(
            TestNetwork._routed_org_vdc_network_name)
        vdcNetwork = VdcNetwork(
            TestNetwork._client, resource=org_vdc_routed_nw)
        result = vdcNetwork.modify_static_ip_pool(TestNetwork._ip_range,
                                                  TestNetwork._new_ip_range)
        task = TestNetwork._client.get_task_monitor().wait_for_success(
            task=result)
        self.assertEqual(task.get('status'), TaskStatus.SUCCESS.value)
        # Verify
        vdcNetwork.reload()
        vdc_routed_nw = vdcNetwork.get_resource()
        ip_scope = vdc_routed_nw.Configuration.IpScopes.IpScope
        ip_ranges = ip_scope.IpRanges.IpRange
        match_found = False
        for ip_range in ip_ranges:
            if (ip_range.StartAddress + '-' + ip_range.EndAddress) == \
                    TestNetwork._new_ip_range:
                match_found = True
        self.assertTrue(match_found)

    def test_0078_remove_static_ip_pool(self):
        vdc = Environment.get_test_vdc(TestNetwork._client)
        org_vdc_routed_nw = vdc.get_routed_orgvdc_network(
            TestNetwork._routed_org_vdc_network_name)
        vdcNetwork = VdcNetwork(
            TestNetwork._client, resource=org_vdc_routed_nw)
        result = vdcNetwork.remove_static_ip_pool(TestNetwork._new_ip_range)
        task = TestNetwork._client.get_task_monitor().wait_for_success(
            task=result)
        self.assertEqual(task.get('status'), TaskStatus.SUCCESS.value)
        # Verification
        vdcNetwork.reload()
        vdc_routed_nw = vdcNetwork.get_resource()
        ip_scope = vdc_routed_nw.Configuration.IpScopes.IpScope
        # IPRanges element will be missing if there was only one IP range
        if not hasattr(ip_scope, 'IpRanges'):
            return
        ip_ranges = ip_scope.IpRanges.IpRange
        match_found = False
        for ip_range in ip_ranges:
            if (ip_range.StartAddress + '-' + ip_range.EndAddress) == \
                    TestNetwork._new_ip_range:
                match_found = True
        self.assertFalse(match_found)

    def _add_routed_vdc_network_metadata(self, vdc_network, metadata_key,
                                         metadata_value):
        task = vdc_network.set_metadata(metadata_key, metadata_value)
        TestNetwork._client.get_task_monitor().wait_for_success(task=task)
        vdc_network.reload()
        self.assertEqual(
            metadata_value,
            vdc_network.get_metadata_value(metadata_key).TypedValue.Value)

    def _update_routed_vdc_network_metadata(self, vdc_network, metadata_key,
                                            updated_metadata_value):
        task = vdc_network.set_metadata(metadata_key, updated_metadata_value)
        TestNetwork._client.get_task_monitor().wait_for_success(task=task)
        vdc_network.reload()
        self.assertEqual(
            updated_metadata_value,
            vdc_network.get_metadata_value(metadata_key).TypedValue.Value)

    def _delete_routed_vcd_network_metadata(self, vdc_network, metadata_key):
        task = vdc_network.remove_metadata(metadata_key)
        TestNetwork._client.get_task_monitor().wait_for_success(task=task)
        vdc_network.reload()
        with self.assertRaises(AccessForbiddenException):
            vdc_network.get_metadata_value(metadata_key)

    def test_0080_routed_vdc_network_metadata(self):
        vdc = Environment.get_test_vdc(TestNetwork._client)
        org_vdc_routed_nw = vdc.get_routed_orgvdc_network(
            TestNetwork._routed_org_vdc_network_name)
        vdc_network = VdcNetwork(
            TestNetwork._client, resource=org_vdc_routed_nw)

        # Test data
        metadata_key = "test-key1"
        metadata_value = "test-value1"
        updated_metadata_value = "updated-" + metadata_value

        # Testing add, update and delete metadata
        TestNetwork._add_routed_vdc_network_metadata(
            self, vdc_network, metadata_key, metadata_value)
        TestNetwork._update_routed_vdc_network_metadata(
            self, vdc_network, metadata_key, updated_metadata_value)
        TestNetwork._delete_routed_vcd_network_metadata(self, vdc_network,
                                                        metadata_key)

    def test_0090_list_routed_vdc_network_allocated_ip(self):
        vdc = Environment.get_test_vdc(TestNetwork._client)
        org_vdc_routed_nw = vdc.get_routed_orgvdc_network(
            TestNetwork._routed_org_vdc_network_name)
        vdc_network = VdcNetwork(
            TestNetwork._client, resource=org_vdc_routed_nw)
        allocated_ip_addresses = vdc_network.list_allocated_ip_address()
        self.assertEqual(len(allocated_ip_addresses), 1)
        ip_address = TestNetwork._routed_orgvdc_network_gateway_ip.split(
            '/')[0]
        self.assertEqual(allocated_ip_addresses[0]['IP Address'], ip_address)

    def test_0100_list_connected_vapps_org_admin(self):
        TestNetwork._list_connected_vapps(self, self._client)

    def test_0110_list_connected_vapps_sys_admin(self):
        TestNetwork._list_connected_vapps(self, self._system_client)

    def _list_connected_vapps(self, client):
        vdc = Environment.get_test_vdc(client)
        vapp_name = 'test-connected-vapp'
        vdc.create_vapp(
            vapp_name, network=TestNetwork._routed_org_vdc_network_name)
        org_vdc_routed_nw = vdc.get_routed_orgvdc_network(
            TestNetwork._routed_org_vdc_network_name)
        vdc_network = VdcNetwork(
            client, resource=org_vdc_routed_nw)
        connected_vapps = vdc_network.list_connected_vapps()
        self.assertEqual(len(connected_vapps), 1)
        self.assertEqual(connected_vapps[0].get('Name'), vapp_name)
        # Delete test vApp after test
        vdc.reload()
        vdc.delete_vapp(vapp_name)

    def test_0120_convert_to_subinterface_org_admin(self):
        TestNetwork.__convert_to_subinterface(self, TestNetwork._client)

    def test_0125_convert_to_subinterface_sys_admin(self):
        TestNetwork.__convert_to_subinterface(self, TestNetwork._system_client)

    def __convert_to_subinterface(self, client):
        vdc = Environment.get_test_vdc(client)
        org_vdc_routed_nw = vdc.get_routed_orgvdc_network(
            TestNetwork._routed_org_vdc_network_name)
        vdc_network = VdcNetwork(client, resource=org_vdc_routed_nw)

        result = vdc_network.convert_to_sub_interface()

        task = TestNetwork._client.get_task_monitor().wait_for_success(
            task=result)
        self.assertEqual(task.get('status'), TaskStatus.SUCCESS.value)

        # Verify
        vdc_network.reload_admin()
        reloaded_vdc_network = vdc_network.admin_resource
        self.assertTrue(reloaded_vdc_network.Configuration.SubInterface)

        # Revert to Internal Interface
        result = vdc_network.convert_to_internal_interface()
        task = TestNetwork._client.get_task_monitor().wait_for_success(
            task=result)
        self.assertEqual(task.get('status'), TaskStatus.SUCCESS.value)

        # Verify
        vdc_network.reload_admin()
        reloaded_vdc_network = vdc_network.admin_resource
        self.assertFalse(reloaded_vdc_network.Configuration.SubInterface)

    def test_0135_convert_to_distributed_interface_sys_admin(self):
        self.__convert_to_distributed_interface(TestNetwork._system_client)

    def test_0140_convert_to_distributed_interface_org_admin(self):
        self.__convert_to_distributed_interface(TestNetwork._client)

    def __convert_to_distributed_interface(self, client):
        self.__convert_enable_dr_in_gateway_using_sys_client(True)

        vdc = Environment.get_test_vdc(client)
        org_vdc_routed_nw = vdc.get_routed_orgvdc_network(
            TestNetwork._routed_org_vdc_network_name)
        vdc_network = VdcNetwork(client, resource=org_vdc_routed_nw)

        result = vdc_network.convert_to_distributed_interface()
        self.__wait_for_success(client, result)

        # Verify
        vdc_network.reload_admin()
        reloaded_vdc_network = vdc_network.admin_resource
        self.assertTrue(
            reloaded_vdc_network.Configuration.DistributedInterface)

        # Revert
        result = vdc_network.convert_to_internal_interface()
        self.__wait_for_success(client, result)

        # Disable the distributed routing on gateway
        self.__convert_enable_dr_in_gateway_using_sys_client(False)

    def __convert_enable_dr_in_gateway_using_sys_client(self, is_enable):
        client = TestNetwork._system_client
        gateway = Environment.get_test_gateway(client)
        if is_enable is True:
            current_state = 'false'
            new_state = 'true'
        else:
            current_state = 'true'
            new_state = 'false'

        if gateway.get('distributedRoutingEnabled') == current_state:
            self.__enable_gateway_distributed_routing(client, gateway,
                                                      is_enable)
            gateway = Environment.get_test_gateway(client)
            self.assertEqual(gateway.get('distributedRoutingEnabled'),
                             new_state)

    def __enable_gateway_distributed_routing(self, client, gateway, is_enable):
        gateway_obj = Gateway(client, href=gateway.get('href'))
        task = gateway_obj.enable_distributed_routing(is_enable)
        self.__wait_for_success(client, task)

    def __wait_for_success(self, client, task):
        result = client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_1000_delete_routed_orgvdc_networks(self):
        vdc = Environment.get_test_vdc(TestNetwork._client)

        result = vdc.delete_routed_orgvdc_network(
            name=TestNetwork._routed_org_vdc_network_name, force=True)
        task = TestNetwork._client.get_task_monitor().wait_for_success(
            task=result)
        self.assertEqual(task.get('status'), TaskStatus.SUCCESS.value)

    @developerModeAware
    def test_9998_teardown(self):
        """Test the method vdc.delete_isolated_orgvdc_network().

        Invoke the method for the orgvdc network created by setup.

        This test passes if the task for deleting the network succeeds.
        """
        logger = Environment.get_default_logger()
        vdc = Environment.get_test_vdc(TestNetwork._client)

        logger.debug('Deleting isolated orgvdc network : ' +
                     TestNetwork._isolated_orgvdc_network_name)
        result = vdc.delete_isolated_orgvdc_network(
            name=TestNetwork._isolated_orgvdc_network_name, force=True)
        TestNetwork._client.get_task_monitor().wait_for_success(task=result)

    def test_9999_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        if TestNetwork._client is not None:
            TestNetwork._client.logout()
        if TestNetwork._vapp_author_client is not None:
            TestNetwork._vapp_author_client.logout()
