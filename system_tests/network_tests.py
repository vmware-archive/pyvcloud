import os
import random
import shutil
import string
import tempfile
import unittest

from pyvcloud.system_test_framework.base_test import BaseTestCase
from pyvcloud.system_test_framework.environment import CommonRoles
from pyvcloud.system_test_framework.environment import developerModeAware
from pyvcloud.system_test_framework.environment import Environment

from pyvcloud.vcd.exceptions import EntityNotFoundException
from pyvcloud.vcd.platform import Platform
from pyvcloud.vcd.client import TaskStatus


class TestNetwork(BaseTestCase):
    """Test network functionalities implemented in pyvcloud."""

    _client = None
    _test_runner_role = CommonRoles.ORGANIZATION_ADMINISTRATOR

    _test_direct_network_name = 'test-direct-vdc-network'
    _test_direct_network_parent_network = 'test-parent-network'

    _test_isolated_network_name = 'test-second-isolated-vdc-network'
    _test_isolated_network_gateway_ip = '10.1.2.1'
    _test_isolated_network_gateway_netmask = '255.255.255.0'

    _test_natrouted_network_name = 'test-natrouted-vdc-network'
    _test_natrouted_network_gateway_name = 'test-vdc-gateway'
    _test_natrouted_network_gateway_ip = '10.1.3.1'
    _test_natrouted_network_gateway_netmask = '255.255.255.0'

    def test_0000_setup(self):
        """Setup the client required for the other tests in this module.
        """
        TestNetwork._client = Environment.get_client_in_default_org(
            TestNetwork._test_runner_role)

    def test_0010_create_direct_orgvdc_network(self):
        vdc = Environment.get_test_vdc(TestNetwork._client)

        result = vdc.create_directly_connected_vdc_network(
            network_name=TestNetwork._test_direct_network_name,
            parent_network_name=TestNetwork._test_direct_network_parent_network,
            description='Dummy description')
        task = client.get_task_monitor().wait_for_success(task=result.Tasks.Task[0])
        self.assertEqual(task.get('status'), TaskStatus.SUCCESS.value)

    def test_0020_create_isolated_orgvdc_network(self):
        vdc = Environment.get_test_vdc(TestNetwork._client)

        result = vdc.create_isolated_vdc_network(
            network_name=TestNetwork._test_isolated_network_name,
            gateway_ip=TestNetwork._test_isolated_network_gateway_ip,
            netmask=TestNetwork._test_isolated_network_gateway_netmask,
            description='Dummy description')
        task = TestNetwork._client.get_task_monitor().wait_for_success(
            task=result.Tasks.Task[0])
        self.assertEqual(task.get('status'), TaskStatus.SUCCESS.value)

    def test_0025_create_natrouted_orgvdc_network(self):
        vdc = Environment.get_test_vdc(TestNetwork._client)

        result = vdc.create_natrouted_vdc_network(
            network_name=TestNetwork._test_natrouted_network_name,
            gateway_name=TestNetwork._test_natrouted_network_gateway_name,
            gateway_ip=TestNetwork._test_natrouted_network_gateway_ip,
            netmask=TestNetwork._test_natrouted_network_gateway_netmask,
            description='Dummy description')
        task = TestNetwork._client.get_task_monitor().wait_for_success(
            task=result.Tasks.Task[0])
        self.assertEqual(task.get('status'), TaskStatus.SUCCESS.value)

    def test_0030_list_external_networks(self):
        vdc = Environment.get_test_vdc(TestNetwork._client)
        platform = Platform(TestNetwork._client)
        ext_net_refs = platform.list_external_networks()
        self.assertTrue(len(ext_net_refs) > 0)

    def test_0040_list_direct_orgvdc_networks(self):
        vdc = Environment.get_test_vdc(TestNetwork._client)
        result = vdc.list_orgvdc_direct_networks()
        self.assertTrue(len(result) > 0)

    def test_0050_list_isolated_orgvdc_networks(self):
        vdc = Environment.get_test_vdc(TestNetwork._client)
        result = vdc.list_orgvdc_isolated_networks()
        self.assertTrue(len(result) > 0)

    def test_0060_list_natrouted_orgvdc_networks(self):
        vdc = Environment.get_test_vdc(TestNetwork._client)
        result = vdc.list_orgvdc_natrouted_networks()
        self.assertTrue(len(result) > 0)

    def test_0190_delete_direct_orgvdc_networks(self):
        vdc = Environment.get_test_vdc(TestNetwork._client)
        result = vdc.delete_direct_orgvdc_network(
            name=TestNetwork._test_direct_network_name, force=True)
        task = TestNetwork._client.get_task_monitor().wait_for_success(
            task=result)
        self.assertEqual(task.get('status'), TaskStatus.SUCCESS.value)

    def test_0200_delete_isolated_orgvdc_networks(self):
        vdc = Environment.get_test_vdc(TestNetwork._client)
        result = vdc.delete_isolated_orgvdc_network(
            name=TestNetwork._test_isolated_network_name, force=True)
        task = TestNetwork._client.get_task_monitor().wait_for_success(
            task=result)
        self.assertEqual(task.get('status'), TaskStatus.SUCCESS.value)

    def test_210_delete_natrouted_orgvdc_networks(self):
        vdc = Environment.get_test_vdc(TestNetwork._client)

        result = vdc.delete_natrouted_orgvdc_network(
            name=TestNetwork._test_natrouted_network_name, force=True)
        task = TestNetwork._client.get_task_monitor().wait_for_success(
            task=result)
        self.assertEqual(task.get('status'), TaskStatus.SUCCESS.value)

    def test_9999_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestNetwork._client.logout()


if __name__ == '__main__':
    unittest.main()
