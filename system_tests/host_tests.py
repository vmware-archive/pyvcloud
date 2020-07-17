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

from pyvcloud.system_test_framework.base_test import BaseTestCase
from pyvcloud.system_test_framework.environment import Environment

from pyvcloud.vcd.exceptions import EntityNotFoundException
from pyvcloud.vcd.platform import Platform


class TestHost(BaseTestCase):
    """Test Host functionalities implemented in pyvcloud."""

    # All tests in this module should be run as System Administrator
    _client = None
    _config = None
    _host_name = None
    _non_existent_host_name = 'non_existent_host'

    def test_0000_setup(self):
        TestHost._client = Environment.get_sys_admin_client()
        TestHost._config = Environment.get_config()
        TestHost._host_name = self._config['host']['host_name']

    def test_0010_list_hosts(self):
        """Platform.list_hosts prints a list of hosts."""
        logger = Environment.get_default_logger()
        platform = Platform(TestHost._client)
        hosts = platform.list_hosts()
        for host in hosts:
            logger.debug('Host found: %s' % host.get('name'))
        self.assertTrue(len(hosts) > 0)

    def test_0020_get_host(self):
        """Platform.get_host finds a known host."""
        logger = Environment.get_default_logger()
        platform = Platform(TestHost._client)
        host = platform.get_host(TestHost._host_name)
        logger.debug('Host: name=%s' % (host.get('name')))
        self.assertIsNotNone(host)

    def test_0030_get_host_negative(self):
        """Platform.get_host does not find a non-existent host."""
        try:
            platform = Platform(TestHost._client)
            platform.get_host(TestHost._non_existent_host_name)
            self.fail('Should not be able to find Host that does not exist ' +
                      TestHost._non_existent_host_name)
        except EntityNotFoundException as e:
            return

    # Enable and disable host tests are commented-out as these methods
    # are deprecated since API version 31.0.

    # def test_0050_enable_host(self):
    #     """Platform.enable_host enables a host.

    #     Wait for async command to complete before checking result.
    #     """
    #     platform = Platform(TestHost._client)

    #     task = platform.enable_disable_host(
    #         name=TestHost._host_name, enable_flag=True)
    #     TestHost._client.get_task_monitor().wait_for_success(task=task)
    #     host = platform.get_host(name=TestHost._host_name)
    #     self.assertTrue(host.IsEnabled)

    # def test_0070_disable_host(self):
    #     """Platform.disable_host disables a host.

    #     Wait for async command to complete before checking result.
    #     """
    #     platform = Platform(TestHost._client)

    #     task = platform.enable_disable_host(
    #         name=TestHost._host_name, enable_flag=False)
    #     TestHost._client.get_task_monitor().wait_for_success(task=task)
    #     host = platform.get_vcenter(name=TestHost._host_name)
    #     self.assertFalse(host.IsEnabled)

    def test_9999_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestHost._client.logout()


if __name__ == '__main__':
    unittest.main()
