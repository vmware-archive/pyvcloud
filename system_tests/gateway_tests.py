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
from pyvcloud.vcd.client import ApiVersion
from pyvcloud.vcd.client import E
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import find_link
from pyvcloud.vcd.client import GatewayBackingConfigType
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import QueryResultFormat
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.client import ResourceType
from pyvcloud.vcd.client import TaskStatus
from pyvcloud.vcd.extension import Extension
from pyvcloud.system_test_framework.base_test import BaseTestCase
from pyvcloud.system_test_framework.environment import CommonRoles
from pyvcloud.system_test_framework.environment import Environment
from pyvcloud.system_test_framework.constants.gateway_constants import \
    GatewayConstants
from pyvcloud.vcd.gateway import Gateway
from pyvcloud.vcd.platform import Platform
from pyvcloud.vcd.utils import netmask_to_cidr_prefix_len


class TestGateway(BaseTestCase):
    """Test Gateway functionalities implemented in pyvcloud."""
    # All tests in this module should be run as System Administrator.
    _client = None
    _name = (GatewayConstants.name + str(uuid1()))[:34]
    _description = GatewayConstants.description + str(uuid1())
    _gateway = None
    _rate_limit_start = '101.0'
    _rate_limit_end = '101.0'

    # Firewall Rule
    _firewall_rule_name = 'Rule Name Test'

    # DHCP pool
    _pool_ip_range = '30.20.10.110-30.20.10.112'

    # DHCP binding
    _mac_address = '00:14:22:01:23:45'
    _host_name = 'xyzName'
    _binding_ip_address = '10.20.30.40'
    _syslog_server_ip1 = '10.40.40.40'

    def test_0000_setup(self):
        """Setup the gateway required for the other tests in this module.

        Create a gateway as per the configuration stated
        above.

        This test passes if the gateway is created successfully.
        """
        TestGateway._client = Environment.get_sys_admin_client()
        TestGateway._vdc = Environment.get_test_vdc(TestGateway._client)

        TestGateway._org_client = Environment.get_client_in_default_org(
            CommonRoles.ORGANIZATION_ADMINISTRATOR)
        TestGateway._config = Environment.get_config()
        TestGateway._api_version = TestGateway._config['vcd']['api_version']

        external_network = Environment.get_test_external_network(
            TestGateway._client)

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
        if float(TestGateway._api_version) <= float(
                ApiVersion.VERSION_30.value):
            TestGateway._gateway = \
                TestGateway._vdc.create_gateway_api_version_30(
                    self._name, [ext_net_resource.get('name')], 'compact',
                    None,
                    True, ext_net_resource.get('name'), gateway_ip, True,
                    False,
                    False, False, True,
                    ext_net_to_participated_subnet_with_ip_settings, True,
                    ext_net_to_subnet_with_ip_range, ext_net_to_rate_limit)
        elif float(TestGateway._api_version) == float(
                ApiVersion.VERSION_31.value):
            TestGateway._gateway = \
                TestGateway._vdc.create_gateway_api_version_31(
                    self._name, [ext_net_resource.get('name')], 'compact',
                    None, True, ext_net_resource.get('name'), gateway_ip,
                    True, False, False, False, True,
                    ext_net_to_participated_subnet_with_ip_settings, True,
                    ext_net_to_subnet_with_ip_range, ext_net_to_rate_limit)
        elif float(TestGateway._api_version) >= float(
                ApiVersion.VERSION_32.value):
            TestGateway._gateway = \
                TestGateway._vdc.create_gateway_api_version_32(
                    self._name, [ext_net_resource.get('name')], 'compact',
                    None, True, ext_net_resource.get('name'), gateway_ip,
                    True, False, False, False, True,
                    ext_net_to_participated_subnet_with_ip_settings, True,
                    ext_net_to_subnet_with_ip_range, ext_net_to_rate_limit)

        result = TestGateway._client.get_task_monitor().wait_for_success(
            task=TestGateway._gateway.Tasks.Task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

        TestGateway._extension = Extension(TestGateway._client)
        TestGateway._extension.get_resource()
        link = find_link(TestGateway._extension.resource, RelationType.DOWN,
                         EntityType.SYSTEM_SETTINGS.value)
        settings = TestGateway._client.get_resource(link.href)
        syslog_server_settings = settings.GeneralSettings.SyslogServerSettings

        if hasattr(syslog_server_settings,
                   '{' + NSMAP['vcloud'] + '}SyslogServerIp1'):
            return
        syslog_server_settings.append(
            E.SyslogServerIp1(TestGateway._syslog_server_ip1))
        TestGateway._client.put_resource(link.href, settings,
                                         EntityType.SYSTEM_SETTINGS.value)
        TestGateway._extension.reload()
        settings = TestGateway._client.get_resource(link.href)
        self.assertTrue(
            hasattr(syslog_server_settings, '{' + NSMAP['vcloud'] +
                    '}SyslogServerIp1'))

    def test_0001_convert_to_advanced(self):
        """Convert the legacy gateway to advance gateway.

        Invoke the convert_to_advanced method for gateway.
        """
        if float(TestGateway._api_version) >= float(
                ApiVersion.VERSION_32.value):
            return
        gateway_obj = Gateway(TestGateway._org_client, self._name,
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
        for client in (TestGateway._client, TestGateway._org_client):
            gateway_obj = Gateway(client, self._name,
                                  TestGateway._gateway.get('href'))
            ip_allocations = gateway_obj.list_external_network_ip_allocations()
            self.assertTrue(bool(ip_allocations))

    def test_0005_redeploy(self):
        """Redeploy the gateway.

        Invoke the redeploy function of gateway.
        """
        for client in (TestGateway._client, TestGateway._org_client):
            gateway_obj = Gateway(client, self._name,
                                  TestGateway._gateway.get('href'))
            task = gateway_obj.redeploy()
            result = TestGateway._client.get_task_monitor().wait_for_success(
                task=task)
            self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0006_sync_syslog_settings(self):
        """Sync syslog settings of the gateway.

        Invoke the sync_syslog_settings function of gateway.
        """
        for client in (TestGateway._client, TestGateway._org_client):
            gateway_obj = Gateway(client, self._name,
                                  TestGateway._gateway.get('href'))
            task = gateway_obj.sync_syslog_settings()
            result = TestGateway._client.get_task_monitor().wait_for_success(
                task=task)
            self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0010_set_tenant_syslog_server_ip(self):
        """Set Tenant syslog server IP of the gateway.

        Invoke the set_tenant_syslog_server_ip function of gateway.
        """

        gateway_obj = Gateway(TestGateway._client, self._name,
                              TestGateway._gateway.get('href'))
        task = gateway_obj.set_tenant_syslog_server_ip('192.168.5.6')
        result = TestGateway._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0015_list_external_network_config_ip_allocations(self):
        """List external network configure ip allocations.

        Invoke the list_gateways_configure_ip_settings of the gateway.
        """
        for client in (TestGateway._client, TestGateway._org_client):
            gateway_obj = Gateway(client, self._name,
                                  TestGateway._gateway.get('href'))
            ip_allocations = gateway_obj.list_configure_ip_settings()
            platform = Platform(TestGateway._client)
            external_networks = platform.list_external_networks()
            self.assertTrue(bool(ip_allocations))
            exnet = ip_allocations[0].get('external_network')
            self.assertEqual(external_networks[0].get('name'), exnet)

    def _create_external_network(self):
        """Creates an external network from the available portgroup."""
        vc_name = TestGateway._config['vc']['vcenter_host_name']
        name_filter = ('vcName', vc_name)
        query = TestGateway._client.get_typed_query(
            ResourceType.PORT_GROUP.value,
            query_result_format=QueryResultFormat.RECORDS,
            equality_filter=name_filter)

        port_group = None
        for record in list(query.execute()):
            if record.get('networkName') == '--':
                if not record.get('name').startswith('vxw-'):
                    port_group = record.get('name')
                    break

        if port_group is None:
            raise Exception(
                'None of the port groups are free for new network.')

        name = 'external_network_' + str(uuid1())
        platform = Platform(TestGateway._client)
        ext_net = platform.create_external_network(
            name=name,
            vim_server_name=vc_name,
            port_group_names=[port_group],
            gateway_ip='10.10.30.1',
            netmask='255.255.255.0',
            ip_ranges=['10.10.30.101-10.10.30.150'],
            description=name,
            primary_dns_ip='8.8.8.8',
            secondary_dns_ip='8.8.8.9',
            dns_suffix='example.com')

        task = ext_net['{' + NSMAP['vcloud'] + '}Tasks'].Task[0]
        TestGateway._client.get_task_monitor().wait_for_success(task=task)
        TestGateway._external_network2 = ext_net
        return ext_net

    def _delete_external_network(self, network):
        logger = Environment.get_default_logger()
        platform = Platform(TestGateway._client)
        task = platform.delete_external_network(network.get('name'))
        TestGateway._client.get_task_monitor().wait_for_success(task=task)
        logger.debug('Deleted external network ' + network.get('name') + '.')

    def test_0020_add_external_network(self):
        """Add an exernal netowrk to the gateway.

        Invoke the add_external_network function of gateway.
        """
        gateway_obj = Gateway(TestGateway._client, self._name,
                              TestGateway._gateway.get('href'))

        extNw2 = self._create_external_network()
        ip_scopes = extNw2.xpath(
            'vcloud:Configuration/vcloud:IpScopes/vcloud:IpScope',
            namespaces=NSMAP)
        first_ipscope = ip_scopes[0]
        gateway_ip = first_ipscope.Gateway.text
        prefixlen = netmask_to_cidr_prefix_len(gateway_ip,
                                               first_ipscope.Netmask.text)
        subnet_addr = gateway_ip + '/' + str(prefixlen)

        task = gateway_obj.add_external_network(
            extNw2.get('name'), [(subnet_addr, 'Auto')])
        result = TestGateway._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0025_remove_external_network(self):
        """Remove an exernal netowrk from the gateway.

        Invoke the remove_external_network function of gateway.
        """
        gateway_obj = Gateway(TestGateway._client, self._name,
                              TestGateway._gateway.get('href'))
        task = gateway_obj.remove_external_network(
            TestGateway._external_network2.get('name'))
        result = TestGateway._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

        self._delete_external_network(TestGateway._external_network2)

    def test_0030_edit_gateway(self):
        """Edit the gateway name.

        Invokes the edit_gateway of the gateway.
        """
        gateway_obj = Gateway(TestGateway._client, self._name,
                              TestGateway._gateway.get('href'))
        task = gateway_obj.edit_gateway(newname='gateway2')
        result = TestGateway._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        '''resetting back to original gateway name'''
        task = gateway_obj.edit_gateway(TestGateway._name)
        result = TestGateway._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0035_edit_config_ipaddress(self):
        """It edits the config ip settings of gateway.
        In this user can only modify Subnet participation and config Ip address
        of gateway's external network.

        Invokes the edit_config_ip_settings of the gateway.
        """
        gateway_obj = Gateway(TestGateway._client, self._name,
                              TestGateway._gateway.get('href'))
        ip_allocations = gateway_obj.list_configure_ip_settings()
        ip_allocation = ip_allocations[0]
        ipconfig = dict()
        subnet_participation = dict()
        subnet = dict()
        subnet_participation['enable'] = True
        subnet_participation['ip_address'] = ip_allocation.get('ip_address')[0]
        subnet[ip_allocation.get('gateway')[0]] = subnet_participation

        ipconfig[ip_allocation.get('external_network')] = subnet
        task = gateway_obj.edit_config_ip_settings(ipconfig)
        result = TestGateway._client.get_task_monitor().wait_for_success(
            task=task)
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

    def test_0040_add_sub_allocated_ip_pools(self):
        """It adds the sub allocated ip pools to gateway.

        Invokes the add_sub_allocated_ip_pools of the gateway.
        """
        gateway_obj = Gateway(TestGateway._client, self._name,
                              TestGateway._gateway.get('href'))
        ip_allocations = gateway_obj.list_configure_ip_settings()
        ip_allocation = ip_allocations[0]
        ext_network = ip_allocation.get('external_network')
        config = TestGateway._config['external_network']
        gateway_sub_allocated_ip_range = \
            config['gateway_sub_allocated_ip_range']
        ip_range_list = [gateway_sub_allocated_ip_range]

        task = gateway_obj.add_sub_allocated_ip_pools(ext_network,
                                                      ip_range_list)
        result = TestGateway._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        gateway_obj = Gateway(TestGateway._client, self._name,
                              TestGateway._gateway.get('href'))
        subnet_participation = self.__get_subnet_participation(
            gateway_obj.get_resource(), ext_network)
        ip_ranges = gateway_obj.get_sub_allocate_ip_ranges_element(
            subnet_participation)
        self.__validate_ip_range(ip_ranges, gateway_sub_allocated_ip_range)

    def test_0045_edit_sub_allocated_ip_pools(self):
        """It edits the sub allocated ip pools of gateway.

        Invokes the edit_sub_allocated_ip_pools of the gateway.
        """
        gateway_obj = Gateway(TestGateway._client, self._name,
                              TestGateway._gateway.get('href'))
        ip_allocations = gateway_obj.list_configure_ip_settings()
        ip_allocation = ip_allocations[0]
        ext_network = ip_allocation.get('external_network')
        config = TestGateway._config['external_network']
        gateway_sub_allocated_ip_range = \
            config['gateway_sub_allocated_ip_range']

        gateway_sub_allocated_ip_range1 = \
            config['new_gateway_sub_allocated_ip_range']

        task = gateway_obj.edit_sub_allocated_ip_pools(
            ext_network, gateway_sub_allocated_ip_range,
            gateway_sub_allocated_ip_range1)
        result = TestGateway._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        gateway_obj = Gateway(TestGateway._client, self._name,
                              TestGateway._gateway.get('href'))
        subnet_participation = self.__get_subnet_participation(
            gateway_obj.get_resource(), ext_network)
        ip_ranges = gateway_obj.get_sub_allocate_ip_ranges_element(
            subnet_participation)
        self.__validate_ip_range(ip_ranges, gateway_sub_allocated_ip_range)

    def test_0050_remove_sub_allocated_ip_pools(self):
        """Remove the sub allocated ip pools of gateway.

        Invokes the remove_sub_allocated_ip_pools of the gateway.
        """
        gateway_obj = Gateway(TestGateway._client, self._name,
                              TestGateway._gateway.get('href'))
        ip_allocations = gateway_obj.list_configure_ip_settings()
        ip_allocation = ip_allocations[0]
        ext_network = ip_allocation.get('external_network')
        config = TestGateway._config['external_network']
        gateway_sub_allocated_ip_range1 = \
            config['new_gateway_sub_allocated_ip_range']

        task = gateway_obj.remove_sub_allocated_ip_pools(
            ext_network, [gateway_sub_allocated_ip_range1])
        result = TestGateway._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        gateway_obj = Gateway(TestGateway._client, self._name,
                              TestGateway._gateway.get('href'))
        subnet_participation = self.__get_subnet_participation(
            gateway_obj.get_resource(), ext_network)
        """removed the IpRanges form subnet_participation."""
        self.assertFalse(hasattr(subnet_participation, 'IpRanges'))

    def test_0055_edit_rate_limit(self):
        """Edits existing rate limit of gateway.

        Invokes the edit_rate_limits of the gateway.
        """
        gateway_obj = Gateway(TestGateway._client, self._name,
                              TestGateway._gateway.get('href'))
        ip_allocations = gateway_obj.list_configure_ip_settings()
        ip_allocation = ip_allocations[0]
        ext_network = ip_allocation.get('external_network')
        config = dict()
        config[ext_network] = [self._rate_limit_start, self._rate_limit_end]

        task = gateway_obj.edit_rate_limits(config)
        result = TestGateway._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        gateway_obj = Gateway(TestGateway._client, self._name,
                              TestGateway._gateway.get('href'))
        for gateway_inf in \
                gateway_obj.get_resource()\
                        .Configuration.GatewayInterfaces.GatewayInterface:
            if gateway_inf.Name == ext_network:
                self.assertEqual(self._rate_limit_start,
                                 gateway_inf.InRateLimit.text)
                self.assertEqual(self._rate_limit_end,
                                 gateway_inf.OutRateLimit.text)

    def test_0060_list_syslog_settings(self):
        """List Tenant syslog server of the gateway.

        Invoke the list_syslog_server_ip function of gateway.
        """
        for client in (TestGateway._client, TestGateway._org_client):
            gateway_obj = Gateway(client, self._name,
                                  TestGateway._gateway.get('href'))
            tenant_syslog_server = gateway_obj.list_syslog_server_ip()
            self.assertGreaterEqual(len(tenant_syslog_server), 1)

    def test_0065_list_rate_limit(self):
        """List rate limit of the gateway.

        Invoke the list_rate_limits function of gateway.
        """
        for client in (TestGateway._client, TestGateway._org_client):
            gateway_obj = Gateway(client, self._name,
                                  TestGateway._gateway.get('href'))
            rate_limit = gateway_obj.list_rate_limits()
            self.assertTrue(len(rate_limit) > 0)

    def __get_gateway_interface(self, gateway, ext_network):
        for gateway_inf in \
                gateway.Configuration.GatewayInterfaces.GatewayInterface:
            if gateway_inf.Name == ext_network:
                return gateway_inf

    def test_0070_disable_rate_limit(self):
        """Disable rate limit of the gateway.

        Invoke the disable_rate_limits function of gateway.
        """
        gateway_obj = Gateway(TestGateway._client, self._name,
                              TestGateway._gateway.get('href'))
        ip_allocations = gateway_obj.list_configure_ip_settings()
        ip_allocation = ip_allocations[0]
        ext_network = ip_allocation.get('external_network')
        gateway_obj = Gateway(TestGateway._client, self._name,
                              TestGateway._gateway.get('href'))
        task = gateway_obj.disable_rate_limits([ext_network])
        result = TestGateway._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        # verification
        gateway_obj = Gateway(TestGateway._client, self._name,
                              TestGateway._gateway.get('href'))
        gateway_interface = self.__get_gateway_interface(
            gateway_obj.get_resource(), ext_network)
        """removed the InRateLimit form gateway_interface."""
        self.assertFalse(hasattr(gateway_interface, 'InRateLimit'))

    def test_0075_configure_gateway(self):
        """configures the gateway.

        Invoke the configure_default_gateway function of gateway.
        """
        gateway_obj = Gateway(TestGateway._client, self._name,
                              TestGateway._gateway.get('href'))
        ip_allocations = gateway_obj.list_configure_ip_settings()
        ip_allocation = ip_allocations[0]
        ext_network = ip_allocation.get('external_network')
        gateway = ip_allocation.get('gateway')
        gateway_ip = gateway[0].split('/')
        gateway_obj = Gateway(TestGateway._client, self._name,
                              TestGateway._gateway.get('href'))
        task = gateway_obj.configure_default_gateway(ext_network,
                                                     gateway_ip[0], 'true')
        result = TestGateway._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        # verification
        gateway_obj = Gateway(TestGateway._client, self._name,
                              TestGateway._gateway.get('href'))
        gateway_interface = self.__get_gateway_interface(
            gateway_obj.get_resource(), ext_network)
        self.assertTrue(gateway_interface.UseForDefaultRoute)

    def test_0080_enable_dns_relay_gateway(self):
        """enables the dns relay of the gateway.

        Invoke the configure_dns_default_gateway function of gateway.
        """
        gateway_obj = Gateway(TestGateway._client, self._name,
                              TestGateway._gateway.get('href'))
        task = gateway_obj.configure_dns_default_gateway('true')
        result = TestGateway._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        # verification
        gateway_obj = Gateway(TestGateway._client, self._name,
                              TestGateway._gateway.get('href'))
        self.assertTrue(gateway_obj.get_resource()
                        .Configuration.UseDefaultRouteForDnsRelay)
        task = gateway_obj.configure_dns_default_gateway('false')
        result = TestGateway._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0085_list_configure_default_gateway(self):
        """list configured default gateway.

        Invoke the list_configure_default_gateway function of gateway.
        """
        gateway_obj = Gateway(TestGateway._client, self._name,
                              TestGateway._gateway.get('href'))
        default_gateways = gateway_obj.list_configure_default_gateway()
        self.assertTrue(len(default_gateways) > 0)

    def test_0090_disable_configure_gateway(self):
        """configures the gateway.

        Invoke the configure_default_gateway function of gateway.
        """
        gateway_obj = Gateway(TestGateway._client, self._name,
                              TestGateway._gateway.get('href'))
        ip_allocations = gateway_obj.list_configure_ip_settings()
        ip_allocation = ip_allocations[0]
        ext_network = ip_allocation.get('external_network')
        gateway = ip_allocation.get('gateway')
        gateway_ip = gateway[0].split('/')
        gateway_obj = Gateway(TestGateway._client, self._name,
                              TestGateway._gateway.get('href'))
        task = gateway_obj.configure_default_gateway(ext_network,
                                                     gateway_ip[0], 'false')
        result = TestGateway._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        # verification
        gateway_obj = Gateway(TestGateway._client, self._name,
                              TestGateway._gateway.get('href'))
        gateway_interface = self.__get_gateway_interface(
            gateway_obj.get_resource(), ext_network)
        self.assertTrue(gateway_interface.UseForDefaultRoute.text == 'false')

    def test_0095_add_firewall_rule(self):
        """Add Firewall Rule's in the gateway."""

        gateway_obj = Gateway(TestGateway._client, self._name,
                              TestGateway._gateway.get('href'))
        gateway_obj.add_firewall_rule(TestGateway._firewall_rule_name)
        firewall_rule = gateway_obj.get_firewall_rules()
        # Verify
        matchFound = False
        for firewallRule in firewall_rule.firewallRules.firewallRule:
            if firewallRule['name'] == TestGateway._firewall_rule_name:
                matchFound = True
                break
        self.assertTrue(matchFound)

    def test_0100_add_dhcp_pool(self):
        """Add DHCP pool in the gateway.
         Invokes the add_dhcp_pool of the gateway.
        """

        gateway_obj = Gateway(
            TestGateway._client, self._name,
            Environment.get_test_gateway(Environment.get_sys_admin_client())
            .get('href'))
        gateway_obj.add_dhcp_pool(TestGateway._pool_ip_range)
        dhcp_resource = gateway_obj.get_dhcp()
        # Verify
        matchFound = False
        for ipPool in dhcp_resource.ipPools.ipPool:
            if ipPool.ipRange.text == TestGateway._pool_ip_range:
                matchFound = True
                break
        self.assertTrue(matchFound)

    def test_0105_add_dhcp_binding(self):
        """Add DHCP Binding in the gateway.

         Invokes the add_dhcp_binding of the gateway.
        """
        gateway_obj = Gateway(
            TestGateway._client, self._name,
            Environment.get_test_gateway(Environment.get_sys_admin_client())
            .get('href'))
        gateway_obj.add_dhcp_binding(TestGateway._mac_address,
                                     TestGateway._host_name,
                                     TestGateway._binding_ip_address)
        dhcp_resource = gateway_obj.get_dhcp()
        # Verify
        matchFound = False
        for static_binding in dhcp_resource.staticBindings.staticBinding:
            if static_binding.macAddress.text == TestGateway._mac_address:
                matchFound = True
                break
        self.assertTrue(matchFound)

    def test_1000_teardown(self):
        """Test the method System.delete_gateway().

        Invoke the method for the gateway created by setup.

        This test passes if no errors are generated while deleting the gateway.
        """
        vdc = Environment.get_test_vdc(TestGateway._client)
        task = vdc.delete_gateway(TestGateway._name)
        result = TestGateway._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_1010_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestGateway._client.logout()


if __name__ == '__main__':
    unittest.main()
