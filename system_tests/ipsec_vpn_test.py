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
from pyvcloud.vcd.client import ApiVersion
from pyvcloud.system_test_framework.base_test import BaseTestCase
from pyvcloud.system_test_framework.environment import Environment
from pyvcloud.system_test_framework.constants.gateway_constants import \
    GatewayConstants
from pyvcloud.vcd.gateway import Gateway
from pyvcloud.vcd.ipsec_vpn import IpsecVpn
from pyvcloud.vcd.system import System
from pyvcloud.vcd.vdc import VDC
from pyvcloud.vcd.vdc_network import VdcNetwork


class TestIpSecVpn(BaseTestCase):
    """Test IpSec VPN functionalities implemented in pyvcloud."""

    # All tests in this module should be run as System Administrator.
    _name = GatewayConstants.name
    _updatedName = 'updatedName'
    _orgvdc_name = 'orgvdc2'
    _gateway_name = 'test_gateway2'
    _routed_network_name = 'routednet2'
    _routed_orgvdc_network_gateway_ip = '10.20.10.1/24'
    _ipsec_vpn_name = 'vpn1'
    _peer_id = 'peer_id1'
    _local_id = 'local_id1'
    _peer_subnet = '10.20.10.0/24'
    _local_subnet = '30.20.10.0/24,30.20.20.0/24'
    _psk = 'abcd1234'
    _changed_psk = "abcdefghijkl"
    _log_level = "warning"

    def test_0000_setup(self):
        """Add one orgvdc, one gateways and one routed orgvdc networks.

        """

        TestIpSecVpn._client = Environment.get_sys_admin_client()
        TestIpSecVpn._config = Environment.get_config()
        TestIpSecVpn._org = Environment.get_test_org(TestIpSecVpn._client)
        TestIpSecVpn._pvdc_name = Environment.get_test_pvdc_name()
        TestIpSecVpn._ext_config = TestIpSecVpn._config['external_network']
        TestIpSecVpn._ext_net_name = TestIpSecVpn._ext_config['name']
        # Create another vdc, gateway and routed network

        self.__create_ovdc()
        self.__create_advanced_gateway()
        self.__create_routed_ovdc_network()

    def test_0010_add_ipsec_vpn(self):
        """Add Ip sec VPN in the gateway.

        Invokes the add_ipsec_vpn of the gateway.
        """

        gateway = Environment.get_test_gateway(TestIpSecVpn._client)
        gateway_obj1 = Gateway(TestIpSecVpn._client, GatewayConstants.name,
                               href=gateway.get('href'))
        TestIpSecVpn._gateway1 = gateway_obj1
        gateway_obj2 = TestIpSecVpn._gateway_obj
        TestIpSecVpn._local_ip = self.__get_ip_address(
            gateway=gateway_obj1, ext_net_name=TestIpSecVpn._ext_net_name)

        TestIpSecVpn._peer_ip = self.__get_ip_address(
            gateway=gateway_obj2, ext_net_name=TestIpSecVpn._ext_net_name)

        gateway_obj1.add_ipsec_vpn(name=TestIpSecVpn._ipsec_vpn_name,
                                   peer_id=TestIpSecVpn._peer_id,
                                   peer_ip_address=TestIpSecVpn._peer_ip,
                                   local_id=TestIpSecVpn._local_id,
                                   local_ip_address=TestIpSecVpn._local_ip,
                                   local_subnet=TestIpSecVpn._local_subnet,
                                   peer_subnet=TestIpSecVpn._peer_subnet,
                                   shared_secret_encrypted=TestIpSecVpn._psk)

        gateway_obj1.reload()
        ipsec_vpn = gateway_obj1.get_ipsec_vpn()
        self.__validate_ip_sec_vpn(ipsec_vpn)

    def test_0015_update_ipsec_vpn(self):
        """Update Ip sec VPN in the gateway.

        Invokes the update_ipsec_vpn of the gateway.
        """
        ipsec_vpn_obj = IpsecVpn(client=TestIpSecVpn._client,
                                 gateway_name=TestIpSecVpn._name,
                                 ipsec_end_point=
                                 TestIpSecVpn._local_ip + "-" +
                                 TestIpSecVpn._peer_ip)

        ipsec_vpn_obj.update_ipsec_vpn(name=TestIpSecVpn._updatedName)
        # Verify
        ipsec_vpn_sites = ipsec_vpn_obj.get_ipsec_config_resource().sites
        for site in ipsec_vpn_sites.site:
            if site.localIp == TestIpSecVpn._local_ip \
                and site.peerIp == TestIpSecVpn._peer_ip:
                self.assertEqual(site.name,TestIpSecVpn._updatedName)
                break

    def __validate_ip_sec_vpn(self, ipsec_vpn):
        site_list = ipsec_vpn.sites.site
        self.assertTrue(len(site_list) > 0)

    def __get_ip_address(self, gateway, ext_net_name):

        gateway_interfaces = gateway.get_resource().Configuration. \
            GatewayInterfaces
        for gateway_inf in gateway_interfaces.GatewayInterface:
            if gateway_inf.Name == ext_net_name:
                return gateway_inf.SubnetParticipation.IpAddress.text

    def test_0020_enable_activation_status(self):
        """Enable activation status.

        Invokes the enable_activation_status of the IpsecVpn.
        """
        gateway_obj1 = TestIpSecVpn._gateway1
        gateway_obj1.enable_activation_status_ipsec_vpn(True)
        # Verify
        activation_status = gateway_obj1.get_ipsec_vpn().enabled
        self.assertTrue(activation_status.text)

    def test_0025_info_activation_status(self):
        """Info activation status.

        Invokes the info_activation_status of the IpsecVpn.
        """
        gateway_obj1 = TestIpSecVpn._gateway1
        status_dict = gateway_obj1.info_activation_status_ipsec_vpn()
        # Verify
        self.assertTrue(status_dict["Activation Status"])

    def test_0030_enable_logging(self):
        """Enable logging.

        Invokes the enable_logging of the IpsecVpn.
        """
        gateway_obj1 = TestIpSecVpn._gateway1
        gateway_obj1.enable_logging_ipsec_vpn(True)
        # Verify
        logging_status = gateway_obj1.get_ipsec_vpn(). \
            logging.enable
        self.assertTrue(logging_status.text)

    def test_0035_change_shared_key(self):
        """Change shared key.

        Invokes the change_shared_key of the IpsecVpn.
        """
        gateway_obj1 = TestIpSecVpn._gateway1
        gateway_obj1.change_shared_key_ipsec_vpn(TestIpSecVpn._changed_psk)
        # Verify
        # verification not possible because values saved in encrypted form.

    def test_0040_set_log_level(self):
        """Set log level.

        Invokes the set_log_level of the IpsecVpn.
        """
        gateway_obj1 = TestIpSecVpn._gateway1
        gateway_obj1.set_log_level_ipsec_vpn(TestIpSecVpn._log_level)
        # Verify
        log_level = gateway_obj1.get_ipsec_vpn(). \
            logging.logLevel
        self.assertEqual(TestIpSecVpn._log_level, log_level)

    def test_0045_info_logging_settings(self):
        """Info logging settings.

        Invokes the info_logging_settings of the IpsecVpn.
        """
        gateway_obj1 = TestIpSecVpn._gateway1
        logging_dict = gateway_obj1.info_logging_settings_ipsec_vpn()
        # Verify
        self.assertTrue(logging_dict["Enable"])

    def test_0050_list_ipsec_vpn(self):
        """List Ipsec Vpn.

        Invokes the list_ipsec_vpn of the IpsecVpn.
        """
        gateway_obj1 = TestIpSecVpn._gateway1
        ipsec_vpn_list = gateway_obj1.list_ipsec_vpn()
        # Verify
        self.assertTrue(len(ipsec_vpn_list) > 0)

    def test_0055_info_ipsec_vpn_site(self):
        """Info Ipsec Vpn site.

        Invokes the get_vpn_site_info of the IpsecVpn.
        """
        ipsec_vpn_obj = IpsecVpn(client=TestIpSecVpn._client,
                                 gateway_name=TestIpSecVpn._name,
                                 ipsec_end_point=
                                 TestIpSecVpn._local_ip + "-" +
                                 TestIpSecVpn._peer_ip)
        site_info = ipsec_vpn_obj.get_vpn_site_info()
        # Verify
        self.assertTrue(len(site_info) > 0)

    def test_0090_delete_ipsec_vpn(self):
        """Delete Ip Sec VPn in the gateway.

        Invokes the delete_ipsec_vpn of the IpsecVpn.
        """
        ipsec_vpn_obj = IpsecVpn(client=TestIpSecVpn._client,
                                 gateway_name=TestIpSecVpn._name,
                                 ipsec_end_point=
                                 TestIpSecVpn._local_ip + "-" +
                                 TestIpSecVpn._peer_ip)

        ipsec_vpn_obj.delete_ipsec_vpn()
        # Verify
        ipsec_vpn_sites = ipsec_vpn_obj.get_ipsec_config_resource().sites
        self.assertFalse(hasattr(ipsec_vpn_sites, "site"))

    def test_0098_teardown(self):
        """Removes the added vdc, gateway and routed networks.

        """
        vdc = VDC(TestIpSecVpn._client, resource=TestIpSecVpn._vdc_resource)
        task1 = vdc.delete_routed_orgvdc_network(
            name=TestIpSecVpn._routed_network_name)
        TestIpSecVpn._client.get_task_monitor().wait_for_success(task=task1)
        task2 = vdc.delete_gateway(name=TestIpSecVpn._gateway_name)
        TestIpSecVpn._client.get_task_monitor().wait_for_success(task=task2)
        vdc.enable_vdc(enable=False)
        vdc.delete_vdc()

    def test_0099_cleanup(self):
        """Release all resources held by this object for testing purposes."""

        TestIpSecVpn._client.logout()

    def __create_ovdc(self):
        """Creates an org vdc with the name specified in the test class.

        :raises: Exception: if the class variable _org_href or _pvdc_name
             is not populated.
         """

        system = System(TestIpSecVpn._client,
                        admin_resource=TestIpSecVpn._client.get_admin())
        if TestIpSecVpn._org is None:
            org_name = TestIpSecVpn._config['vcd']['default_org_name']
            org_resource_list = TestIpSecVpn._client.get_org_list()

        org = TestIpSecVpn._org
        ovdc_name = TestIpSecVpn._orgvdc_name

        if self.__check_ovdc(org, ovdc_name):
            return

        storage_profiles = [{
            'name':
                TestIpSecVpn._config['vcd']['default_storage_profile_name'],
            'enabled':
                True,
            'units':
                'MB',
            'limit':
                0,
            'default':
                True
        }]

        netpool_to_use = Environment._get_netpool_name_to_use(system)
        vdc_resource = org.create_org_vdc(
            ovdc_name,
            TestIpSecVpn._pvdc_name,
            network_pool_name=netpool_to_use,
            network_quota=TestIpSecVpn._config['vcd']['default_network_quota'],
            storage_profiles=storage_profiles,
            uses_fast_provisioning=True,
            is_thin_provision=True)

        TestIpSecVpn._client.get_task_monitor().wait_for_success(
            task=vdc_resource.Tasks.Task[0])

        org.reload()
        # The following contraption is required to get the non admin href of
        # the ovdc. vdc_resource contains the admin version of the href since
        # we created the ovdc as a sys admin.

        self.__check_ovdc(org, ovdc_name)

    def __check_ovdc(self, org, ovdc_name):
        if org.get_vdc(ovdc_name):
            vdc = org.get_vdc(ovdc_name)
            TestIpSecVpn._ovdc_href = vdc.get('href')
            TestIpSecVpn._vdc_resource = vdc
            return True
        else:
            return False

    def __does_exist_gateway(self, gateway_name):
        vdc = VDC(TestIpSecVpn._client, resource=TestIpSecVpn._vdc_resource)
        gateway = vdc.get_gateway(TestIpSecVpn._gateway_name)
        if gateway:
            TestIpSecVpn._gateway_resource = gateway
            TestIpSecVpn._gateway_href = gateway.get('href')
            TestIpSecVpn._gateway_obj = Gateway(
                TestIpSecVpn._client, href=TestIpSecVpn._gateway_href)
            return True
        else:
            return False

    def __create_advanced_gateway(self):
        """Creates a gateway."""

        ext_config = TestIpSecVpn._config['external_network']
        vdc_reource = TestIpSecVpn._vdc_resource
        api_version = TestIpSecVpn._config['vcd']['api_version']
        vdc = VDC(TestIpSecVpn._client, resource=vdc_reource)
        gateway = vdc.get_gateway(TestIpSecVpn._gateway_name)
        if self.__does_exist_gateway(TestIpSecVpn._gateway_name):
            return

        if float(api_version) <= float(
                ApiVersion.VERSION_30.value):
            gateway = vdc.create_gateway_api_version_30(
                TestIpSecVpn._gateway_name, [ext_config['name']])
        elif float(api_version) == float(ApiVersion.VERSION_31.value):
            gateway = vdc.create_gateway_api_version_31(
                TestIpSecVpn._gateway_name,
                [ext_config['name']],
                should_create_as_advanced=True)
        elif float(api_version) >= float(ApiVersion.VERSION_32.value):
            gateway = vdc.create_gateway_api_version_32(
                TestIpSecVpn._gateway_name, [ext_config['name']],
                should_create_as_advanced=True)

        TestIpSecVpn._client.get_task_monitor(). \
            wait_for_success(task=gateway.Tasks.Task[0])
        TestIpSecVpn._gateway_href = gateway.get('href')
        TestIpSecVpn._gateway_obj = Gateway(TestIpSecVpn._client,
                                            href=TestIpSecVpn._gateway_href)
        TestIpSecVpn._gateway_resource = TestIpSecVpn. \
            _gateway_obj.get_resource()

    def __create_routed_ovdc_network(self):
        """Creates a routed org vdc network.

        :raises: Exception: if the class variable _ovdc_href is not populated.
        """
        vdc_reource = TestIpSecVpn._vdc_resource
        vdc = VDC(TestIpSecVpn._client, resource=vdc_reource)
        routednet = vdc.create_routed_vdc_network(
            network_name=TestIpSecVpn._routed_network_name,
            gateway_name=TestIpSecVpn._gateway_name,
            network_cidr=TestIpSecVpn._routed_orgvdc_network_gateway_ip,
            description='org vdc network description')
        TestIpSecVpn._client.get_task_monitor() \
            .wait_for_success(task=routednet.Tasks.Task[0])

        TestIpSecVpn._routednet_href = routednet.get('href')
        TestIpSecVpn._routednet_obj = VdcNetwork(TestIpSecVpn._client,
                                                 href=TestIpSecVpn.
                                                 _routednet_href)
        TestIpSecVpn._routednet_resource = TestIpSecVpn. \
            _routednet_obj.get_resource()

    if __name__ == '__main__':
        unittest.main()
