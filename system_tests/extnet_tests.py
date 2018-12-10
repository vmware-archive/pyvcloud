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

from pyvcloud.system_test_framework.base_test import BaseTestCase
from pyvcloud.system_test_framework.environment import developerModeAware
from pyvcloud.system_test_framework.environment import Environment
from pyvcloud.vcd.external_network import ExternalNetwork

from pyvcloud.vcd.platform import Platform

from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import QueryResultFormat
from pyvcloud.vcd.client import ResourceType


class TestExtNet(BaseTestCase):
    """Test external network functionalities implemented in pyvcloud."""

    # All tests in this module should run as System Administrator.
    _sys_admin_client = None
    _name = 'external_network_' + str(uuid1())
    _description = 'Description of external_network_' + str(uuid1())
    _port_group = None
    _gateway = '10.20.30.1'
    _netmask = '255.255.255.0'
    _ip_range = '10.20.30.2-10.20.30.99'
    _dns1 = '8.8.8.8'
    _dns2 = '8.8.8.9'
    _portgroupType = "DV_PORTGROUP"
    _dns_suffix = 'example.com'
    _gateway2 = '10.10.30.1'
    _ip_range2 = '10.10.30.2-10.10.30.99'
    _ip_range3 = '10.10.30.101-10.10.30.120'
    _ip_range4 = '10.10.30.25-10.10.30.30'

    def test_0000_setup(self):
        """
        Create one external network as per the configuration stated aboveself.

        Choose first unused port group which is not a VxLAN. Unused port groups
        have network names set to '--'. VxLAN port groups have name starting
        with 'vxw-'.

        Test the method Platform.create_external_network().

        This test passes if external network is created successfully.
        """
        logger = Environment.get_default_logger()
        TestExtNet._sys_admin_client = Environment.get_sys_admin_client()
        TestExtNet._config = Environment.get_config()

        platform = Platform(TestExtNet._sys_admin_client)
        vc_name = TestExtNet._config['vc']['vcenter_host_name']
        name_filter = ('vcName', vc_name)
        query = TestExtNet._sys_admin_client.get_typed_query(
            ResourceType.PORT_GROUP.value,
            query_result_format=QueryResultFormat.RECORDS,
            equality_filter=name_filter)

        for record in list(query.execute()):
            if record.get('networkName') == '--':
                if record.get('portgroupType') == TestExtNet._portgroupType \
                    and not record.get('name').startswith('vxw-'):
                    TestExtNet._port_group = record.get('name')
                    break

        self.assertIsNotNone(self._port_group,
                             'None of the port groups are free.')

        ext_net = platform.create_external_network(
            name=TestExtNet._name,
            vim_server_name=vc_name,
            port_group_names=[TestExtNet._port_group],
            gateway_ip=TestExtNet._gateway,
            netmask=TestExtNet._netmask,
            ip_ranges=[TestExtNet._ip_range],
            description=TestExtNet._description,
            primary_dns_ip=TestExtNet._dns1,
            secondary_dns_ip=TestExtNet._dns2,
            dns_suffix=TestExtNet._dns_suffix)

        task = ext_net['{' + NSMAP['vcloud'] + '}Tasks'].Task[0]
        TestExtNet._sys_admin_client.get_task_monitor().wait_for_success(
            task=task)

        logger.debug('Created external network ' + TestExtNet._name + '.')

    def test_0010_update(self):
        """Test the method Platform.update_external_network()

        Update name and description of the external network created by setup.
        Verifies name and description after update completes. Reset the name
        and description to original.

        This test passes if name and description are updated successfully.
        """
        logger = Environment.get_default_logger()
        platform = Platform(TestExtNet._sys_admin_client)
        new_name = 'updated_' + TestExtNet._name
        new_description = 'Updated ' + TestExtNet._description

        ext_net = platform.update_external_network(TestExtNet._name, new_name,
                                                   new_description)

        task = ext_net['{' + NSMAP['vcloud'] + '}Tasks'].Task[0]
        TestExtNet._sys_admin_client.get_task_monitor().wait_for_success(
            task=task)
        logger.debug('Updated external network ' + TestExtNet._name + '.')

        ext_net = platform.get_external_network(new_name)
        self.assertIsNotNone(ext_net)
        self.assertEqual(new_description,
                         ext_net['{' + NSMAP['vcloud'] + '}Description'].text)

        # Reset the name and description to original
        ext_net = platform.update_external_network(new_name, self._name,
                                                   self._description)
        task = ext_net['{' + NSMAP['vcloud'] + '}Tasks'].Task[0]
        TestExtNet._sys_admin_client.get_task_monitor().wait_for_success(
            task=task)

    def test_0020_add_subnet(self):
        """Test the method externalNetwork.add_subnet()

        Add subnet to the existing external network

        This test passes if subnet is added successfully.
        """
        logger = Environment.get_default_logger()
        platform = Platform(TestExtNet._sys_admin_client)
        ext_net_resource = platform.get_external_network(self._name)
        extnet_obj = ExternalNetwork(TestExtNet._sys_admin_client,
                                     resource=ext_net_resource)

        ext_net = extnet_obj.add_subnet(self._name,
                                        TestExtNet._gateway2,
                                        TestExtNet._netmask,
                                        [TestExtNet._ip_range2],
                                        TestExtNet._dns1,
                                        TestExtNet._dns2,
                                        TestExtNet._dns_suffix)

        task = ext_net['{' + NSMAP['vcloud'] + '}Tasks'].Task[0]
        TestExtNet._sys_admin_client.get_task_monitor().wait_for_success(
            task=task)
        logger.debug(
            'Added subnet to external network ' + TestExtNet._name + '.')

        ext_net = platform.get_external_network(self._name)
        self.assertIsNotNone(ext_net)
        config = ext_net['{' + NSMAP['vcloud'] + '}Configuration']
        new_subnet = config.IpScopes.IpScope[-1]
        self.assertEqual(TestExtNet._gateway2, new_subnet.Gateway.text)
        self.assertEqual(TestExtNet._netmask, new_subnet.Netmask.text)

    def test_0030_enable_subnet(self):
        """Test the method externalNetwork.enable_subnet()

        Enable subnet of external network

        This test passes if subnet is enabled successfully.
        """
        logger = Environment.get_default_logger()
        platform = Platform(TestExtNet._sys_admin_client)

        ext_net = self._get_ext_net(platform).enable_subnet(
            TestExtNet._gateway2, True)

        task = ext_net['{' + NSMAP['vcloud'] + '}Tasks'].Task[0]
        TestExtNet._sys_admin_client.get_task_monitor().wait_for_success(
            task=task)
        logger.debug(
            'Enabled subnet of external network ' + TestExtNet._name + '.')

        ext_net = platform.get_external_network(self._name)
        self.assertIsNotNone(ext_net)
        config = ext_net['{' + NSMAP['vcloud'] + '}Configuration']
        ip_scope = config.IpScopes.IpScope
        for scope in ip_scope:
            if scope.Gateway == TestExtNet._gateway2:
                ip_scope = scope
                break
        self.assertIsNotNone(ip_scope)
        self.assertEqual(ip_scope.IsEnabled, True)

    def test_0040_add_ip_range(self):
        """Test the method externalNetwork.add_ip_range()

        Add ip range to a subnet of external network

        This test passes if ip range is added successfully for a subnet.
        """
        logger = Environment.get_default_logger()
        platform = Platform(TestExtNet._sys_admin_client)
        ext_net = self._get_ext_net(platform).add_ip_range(
            TestExtNet._gateway2,
            [TestExtNet._ip_range3])

        task = ext_net['{' + NSMAP['vcloud'] + '}Tasks'].Task[0]
        TestExtNet._sys_admin_client.get_task_monitor().wait_for_success(
            task=task)
        logger.debug(
            'Added new ip-range to a subnet of external network '
            + TestExtNet._name + '.')

        ext_net = platform.get_external_network(self._name)
        self.assertIsNotNone(ext_net)
        config = ext_net['{' + NSMAP['vcloud'] + '}Configuration']
        ip_scope = config.IpScopes.IpScope
        for scope in ip_scope:
            if scope.Gateway == TestExtNet._gateway2:
                ip_scope = scope
                break
        self.assertIsNotNone(ip_scope)
        self.__validate_ip_range(ip_scope, TestExtNet._ip_range3)

    def test_0050_modify_ip_range(self):
        """Test the method externalNetwork.modify_ip_range()
       Modify ip range of a subnet in external network
       This test passes if the ip range for a subnet is
       modified successfully.
       """
        logger = Environment.get_default_logger()
        platform = Platform(TestExtNet._sys_admin_client)
        ext_net = self._get_ext_net(platform).modify_ip_range(
            TestExtNet._gateway2,
            TestExtNet._ip_range2,
            TestExtNet._ip_range4)

        task = ext_net['{' + NSMAP['vcloud'] + '}Tasks'].Task[0]
        TestExtNet._sys_admin_client.get_task_monitor().wait_for_success(
        task=task)
        logger.debug(
        'Modify ip-range of a subnet in external network'
        + TestExtNet._name + '.')

        ext_net = platform.get_external_network(self._name)
        self.assertIsNotNone(ext_net)
        config = ext_net['{' + NSMAP['vcloud'] + '}Configuration']
        ip_scope = config.IpScopes.IpScope
        for scope in ip_scope:
            if scope.Gateway == TestExtNet._gateway2:
                 ip_scope = scope
                 break
        self.assertIsNotNone(ip_scope)
        self.__validate_ip_range(ip_scope, TestExtNet._ip_range4)

    def __validate_ip_range(self, ip_scope, _ip_range1):
        """ Validate if the ip range present in the existing ip ranges """
        _ip_ranges = _ip_range1.split('-')
        _ip_range1_start_address = _ip_ranges[0]
        _ip_range1_end_address = _ip_ranges[1]
        for ip_range in ip_scope.IpRanges.IpRange:
            if ip_range.StartAddress == _ip_range1_start_address:
                self.assertEqual(ip_range.EndAddress, _ip_range1_end_address)

    def test_0060_attach_port_group(self):
        """Attach a portgroup to an external network in external network
       This test passes if the ip range for a subnet is
       modified successfully.
       """
        logger = Environment.get_default_logger()
        platform = Platform(TestExtNet._sys_admin_client)
        vim_server_name = TestExtNet._config['vc']['vcenter1_host_name']
        self.__set_pg_group_name(vim_server_name)
        ext_net = self._get_ext_net(platform).attach_port_group(
            vim_server_name,
            TestExtNet._port_group)
        task = ext_net['{' + NSMAP['vcloud'] + '}Tasks'].Task[0]
        TestExtNet._sys_admin_client.get_task_monitor().wait_for_success(
        task=task)
        logger.debug(
        'Attach a portgroup to an external network'
        + TestExtNet._name + '.')
        ext_net = platform.get_external_network(self._name)
        self.assertIsNotNone(ext_net)
        vc_record = platform.get_vcenter(vim_server_name)
        vc_href = vc_record.get('href')
        vim_port_group_refs = \
            ext_net['{' + NSMAP['vmext'] + '}VimPortGroupRefs']
        vc_href_found = False
        for vim_obj_ref in vim_port_group_refs.VimObjectRef:
            if vim_obj_ref.VimServerRef.get('href') == vc_href:
                vc_href_found = True
                break
        self.assertTrue(vc_href_found)

    def __set_pg_group_name(self, vim_server_name):
        name_filter = ('vcName', vim_server_name)
        query = TestExtNet._sys_admin_client.get_typed_query(
            ResourceType.PORT_GROUP.value,
            query_result_format=QueryResultFormat.RECORDS,
            equality_filter=name_filter)
        for record in list(query.execute()):
            if record.get('networkName') == '--':
                if record.get('portgroupType') == TestExtNet._portgroupType \
                    and not record.get('name').startswith('vxw-') :
                    TestExtNet._port_group = record.get('name')
                    break
        self.assertIsNotNone(TestExtNet._port_group,
            msg="Multiple vCenters not attached to vcd or"
                     "no portgroups available in vCenter")

    @developerModeAware
    def test_9998_teardown(self):
        """Test the method Platform.delete_external_network().

        Invoke the method for the external network created by setup.

        This test passes if the task for deleting the external network
        succeeds.
        """
        logger = Environment.get_default_logger()
        platform = Platform(TestExtNet._sys_admin_client)
        task = platform.delete_external_network(TestExtNet._name)
        TestExtNet._sys_admin_client.get_task_monitor().wait_for_success(
            task=task)
        logger.debug('Deleted external network ' + TestExtNet._name + '.')

    def test_9999_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestExtNet._sys_admin_client.logout()

    def _get_ext_net(self, platform):
        ext_net_resource = platform.get_external_network(self._name)
        return ExternalNetwork(TestExtNet._sys_admin_client,
                               resource=ext_net_resource)

if __name__ == '__main__':
    unittest.main()
