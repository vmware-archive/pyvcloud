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

from helpers.portgroup_helper import PortgroupHelper
from pyvcloud.system_test_framework.base_test import BaseTestCase
from pyvcloud.system_test_framework.environment import developerModeAware
from pyvcloud.system_test_framework.environment import Environment
from pyvcloud.vcd.external_network import ExternalNetwork

from pyvcloud.vcd.platform import Platform

from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.gateway import Gateway


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
    _portgroupType = "NETWORK"
    _dns_suffix = 'example.com'
    _gateway2 = '10.10.30.1'
    _ip_range2 = '10.10.30.2-10.10.30.99'
    _ip_range3 = '10.10.30.101-10.10.30.120'
    _ip_range4 = '10.10.30.25-10.10.30.30'
    _gateway_sub_allocate_ip_pool_range = '2.2.3.10-2.2.3.20'

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
        TestExtNet._common_ext_net_name = TestExtNet._config[
            'external_network']['name']

        platform = Platform(TestExtNet._sys_admin_client)
        vc_name = TestExtNet._config['vc']['vcenter_host_name']
        TestExtNet._vc2_host_ip = TestExtNet._config['vc2']['vcenter_host_ip']
        portgrouphelper = PortgroupHelper(TestExtNet._sys_admin_client)
        pg_name = portgrouphelper.get_available_portgroup_name(
            vc_name, TestExtNet._portgroupType)

        ext_net = platform.create_external_network(
            name=TestExtNet._name,
            vim_server_name=vc_name,
            port_group_names=[pg_name],
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
        self.assertTrue(self.__validate_ip_range(ip_scope,
                                                 TestExtNet._ip_range3))

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
        self.assertTrue(self.__validate_ip_range(ip_scope,
                                                 TestExtNet._ip_range4))

    def test_0055_delete_ip_range(self):
        """Test the method externalNetwork.delete_ip_range()
       Delete ip range of a subnet in external network
       This test passes if the ip range for a subnet is
       deleted successfully.
       """
        logger = Environment.get_default_logger()
        platform = Platform(TestExtNet._sys_admin_client)
        ext_net = self._get_ext_net(platform).delete_ip_range(
            TestExtNet._gateway2,
            [TestExtNet._ip_range4])

        task = ext_net['{' + NSMAP['vcloud'] + '}Tasks'].Task[0]
        TestExtNet._sys_admin_client.get_task_monitor().wait_for_success(
            task=task)
        logger.debug(
            'Deleted ip-range of a subnet in external network'
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
        self.assertFalse(self.__validate_ip_range(ip_scope,
                                                  TestExtNet._ip_range4))

    def __validate_ip_range(self, ip_scope, _ip_range1):
        """ Validate if the ip range present in the existing ip ranges """
        _ip_ranges = _ip_range1.split('-')
        _ip_range1_start_address = _ip_ranges[0]
        _ip_range1_end_address = _ip_ranges[1]
        for ip_range in ip_scope.IpRanges.IpRange:
            if ip_range.StartAddress == _ip_range1_start_address and \
                    ip_range.EndAddress == _ip_range1_end_address:
                return True
        return False

    def test_0060_attach_port_group(self):
        """Attach a portgroup to an external network
       This test passes if the portgroup from another vCenter is added
       to external network successfully.
       """
        if TestExtNet._vc2_host_ip is None or TestExtNet._vc2_host_ip == '':
            return
        logger = Environment.get_default_logger()
        platform = Platform(TestExtNet._sys_admin_client)
        vc_name = TestExtNet._config['vc2']['vcenter_host_name']
        portgrouphelper = PortgroupHelper(TestExtNet._sys_admin_client)
        pg_name = portgrouphelper.get_available_portgroup_name(
            vc_name, TestExtNet._portgroupType)

        ext_net = self._get_ext_net(platform).attach_port_group(
            vc_name,
            pg_name)
        task = ext_net['{' + NSMAP['vcloud'] + '}Tasks'].Task[0]
        TestExtNet._sys_admin_client.get_task_monitor().wait_for_success(
            task=task)
        logger.debug(
            'Attach a portgroup to an external network'
            + TestExtNet._name + '.')
        ext_net = platform.get_external_network(self._name)
        self.assertIsNotNone(ext_net)
        vc_record = platform.get_vcenter(vc_name)
        vc_href = vc_record.get('href')
        vim_port_group_refs = \
            ext_net['{' + NSMAP['vmext'] + '}VimPortGroupRefs']
        vc_href_found = False
        for vim_obj_ref in vim_port_group_refs.VimObjectRef:
            if vim_obj_ref.VimServerRef.get('href') == vc_href:
                vc_href_found = True
                break
        self.assertTrue(vc_href_found)

    def test_0061_detach_port_group(self):
        """Detach a portgroup from an external network
       This test passes if the portgroup from another vCenter is removed
       from external network successfully.
       """
        if TestExtNet._vc2_host_ip is None or TestExtNet._vc2_host_ip == '':
            return
        logger = Environment.get_default_logger()
        platform = Platform(TestExtNet._sys_admin_client)
        vc_name = TestExtNet._config['vc2']['vcenter_host_name']
        port_group_helper = PortgroupHelper(TestExtNet._sys_admin_client)
        pg_name = port_group_helper.get_ext_net_portgroup_name(vc_name,
                                                               self._name)

        ext_net = self._get_ext_net(platform).detach_port_group(vc_name,
                                                                pg_name)
        task = ext_net['{' + NSMAP['vcloud'] + '}Tasks'].Task[0]
        TestExtNet._sys_admin_client.get_task_monitor().wait_for_success(
            task=task)
        logger.debug(
            'Detach a portgroup from an external network' + TestExtNet._name)
        ext_net = platform.get_external_network(self._name)
        self.assertIsNotNone(ext_net)
        vc_record = platform.get_vcenter(vc_name)
        vc_href = vc_record.get('href')
        vim_port_group_ref = ext_net.VimPortGroupRef
        vc_href_found = False

        if vim_port_group_ref.VimServerRef.get('href') == vc_href:
            vc_href_found = True
        self.assertFalse(vc_href_found)

    def test_0065_list_available_pvdc(self):
        """List available provider Vdcs.
        """
        platform = Platform(TestExtNet._sys_admin_client)
        ext_net_resource = platform.get_external_network(
            TestExtNet._common_ext_net_name)
        extnet_obj = ExternalNetwork(TestExtNet._sys_admin_client,
                                     resource=ext_net_resource)
        pvdc_name_list = extnet_obj.list_provider_vdc()
        # Not adding assert because there can be no pvdc associated with the
        # provided external network

    def test_0070_list_available_pvdc_with_filter(self):
        """List available provider Vdcs.
        """
        platform = Platform(TestExtNet._sys_admin_client)
        ext_net_resource = platform.get_external_network(
            TestExtNet._common_ext_net_name)
        extnet_obj = ExternalNetwork(TestExtNet._sys_admin_client,
                                     resource=ext_net_resource)
        pvdc_name_list = extnet_obj.list_provider_vdc('name==*')
        # Not adding assert because there can be no pvdc associated with the
        # provided external network

    def test_0075_list_available_gateways(self):
        """List available gateways.
        """
        platform = Platform(TestExtNet._sys_admin_client)
        ext_net_name = TestExtNet._config['external_network']['name']
        ext_net_resource = platform.get_external_network(ext_net_name)
        extnet_obj = ExternalNetwork(TestExtNet._sys_admin_client,
                                     resource=ext_net_resource)
        gateway_name_list = extnet_obj.list_extnw_gateways()
        self.assertTrue(len(gateway_name_list) > 0)

    def test_0080_list_available_gateways_with_filter(self):
        """List available gateways.
        """
        platform = Platform(TestExtNet._sys_admin_client)
        ext_net_name = TestExtNet._config['external_network']['name']
        ext_net_resource = platform.get_external_network(ext_net_name)
        extnet_obj = ExternalNetwork(TestExtNet._sys_admin_client,
                                     resource=ext_net_resource)
        gateway_name_list = extnet_obj.list_extnw_gateways('name==*')
        self.assertTrue(len(gateway_name_list) > 0)

    def test_0085_list_allocated_ip(self):
        """List allocated ip.
        """
        platform = Platform(TestExtNet._sys_admin_client)
        ext_net_name = TestExtNet._config['external_network']['name']
        ext_net_resource = platform.get_external_network(ext_net_name)
        extnet_obj = ExternalNetwork(TestExtNet._sys_admin_client,
                                     resource=ext_net_resource)
        allocated_ip_dict = extnet_obj.list_allocated_ip_address()
        self.assertTrue(len(allocated_ip_dict) > 0)

    def test_0090_list_allocated_ip_with_gateway_filter(self):
        """List allocated ips.
        """
        platform = Platform(TestExtNet._sys_admin_client)
        ext_net_name = TestExtNet._config['external_network']['name']
        ext_net_resource = platform.get_external_network(ext_net_name)
        extnet_obj = ExternalNetwork(TestExtNet._sys_admin_client,
                                     resource=ext_net_resource)
        allocated_ip_dict = extnet_obj.list_allocated_ip_address('name==*')
        self.assertTrue(len(allocated_ip_dict) > 0)

    def test_0095_list_sub_allocated_ip(self):
        """List sub allocated ip.
        """
        self.__add_sub_allocate_ip_pool()
        platform = Platform(TestExtNet._sys_admin_client)
        ext_net_name = TestExtNet._config['external_network']['name']
        ext_net_resource = platform.get_external_network(ext_net_name)
        extnet_obj = ExternalNetwork(TestExtNet._sys_admin_client,
                                     resource=ext_net_resource)
        sub_allocated_ip_dict = extnet_obj.list_gateway_ip_suballocation()
        self.assertTrue(len(sub_allocated_ip_dict) > 0)

    def test_0096_list_sub_allocated_ip_with_gateway_filter(self):
        """List sub allocated ips.
        """
        platform = Platform(TestExtNet._sys_admin_client)
        ext_net_name = TestExtNet._config['external_network']['name']
        ext_net_resource = platform.get_external_network(ext_net_name)
        extnet_obj = ExternalNetwork(TestExtNet._sys_admin_client,
                                     resource=ext_net_resource)
        sub_allocated_ip_dict = \
            extnet_obj.list_gateway_ip_suballocation('name==*')
        self.assertTrue(len(sub_allocated_ip_dict) > 0)
        self.__remove_sub_allocate_ip_pool()

    def test_0100_list_associated_direct_org_vdc_networks(self):
        """List associated direct org vDC networks
        """
        platform = Platform(TestExtNet._sys_admin_client)
        ext_net_resource = platform.get_external_network(
            TestExtNet._common_ext_net_name)
        extnet_obj = ExternalNetwork(TestExtNet._sys_admin_client,
                                     resource=ext_net_resource)
        ovdc_network_name = 'test-direct-vdc-network'
        filter = 'name==' + ovdc_network_name
        direct_ovdc_networks = \
            extnet_obj.list_associated_direct_org_vdc_networks(filter)
        match_found = False
        if ovdc_network_name in direct_ovdc_networks:
            match_found = True
        self.assertTrue(match_found)

    def test_0105_list_vsphere_network(self):
        """List associated vSphere Networks.
        """
        platform = Platform(TestExtNet._sys_admin_client)
        ext_net_resource = platform.get_external_network(
            TestExtNet._name)
        extnet_obj = ExternalNetwork(TestExtNet._sys_admin_client,
                                     resource=ext_net_resource)
        portgroup_name = 'VM Network'
        vSphere_network_list = \
            extnet_obj.list_vsphere_network('name==' + portgroup_name)
        match_found = False
        for dic in vSphere_network_list:
            if dic['Name'] == portgroup_name:
                match_found = True
        self.assertTrue(match_found)

    def __add_sub_allocate_ip_pool(self):
        gateway = Environment. \
            get_test_gateway(TestExtNet._sys_admin_client)
        gateway_obj = Gateway(TestExtNet._sys_admin_client,
                              href=gateway.get('href'))
        ext_net = TestExtNet._config['external_network']['name']
        task = gateway_obj.add_sub_allocated_ip_pools(
            ext_net, [TestExtNet._gateway_sub_allocate_ip_pool_range])
        TestExtNet._sys_admin_client.get_task_monitor(). \
            wait_for_success(task=task)

    def __remove_sub_allocate_ip_pool(self):
        gateway = Environment. \
            get_test_gateway(TestExtNet._sys_admin_client)
        gateway_obj = Gateway(TestExtNet._sys_admin_client,
                              href=gateway.get('href'))
        ext_net = TestExtNet._config['external_network']['name']
        task = gateway_obj.remove_sub_allocated_ip_pools(
            ext_net, [TestExtNet._gateway_sub_allocate_ip_pool_range])
        TestExtNet._sys_admin_client.get_task_monitor(). \
            wait_for_success(task=task)

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
