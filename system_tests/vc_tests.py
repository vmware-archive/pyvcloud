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

from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.platform import Platform


class TestVC(BaseTestCase):

    def test_0000_setup(self):
        TestVC._client = Environment.get_sys_admin_client()
        TestVC._config = Environment.get_config()
        TestVC._vcenter_host_name = self._config['vc']['vcenter_host_name']
        TestVC._vcenter_invalid = self._config['vc']['vcenter_invalid']
        TestVC._vcServerName = self._config['vc']['vcServerName']
        TestVC._vcServerHost = self._config['vc']['vcServerHost']
        TestVC._vcAdminUser = self._config['vc']['vcAdminUser']
        TestVC._vcAdminPwd = self._config['vc']['vcAdminPwd']
        TestVC._NSXServerName = self._config['vc']['NSXServerName']
        TestVC._NSXHost = self._config['vc']['NSXHost']
        TestVC._NSXAdminUser = self._config['vc']['NSXAdminUser']
        TestVC._NSXAdminPwd = self._config['vc']['NSXAdminPwd']
        TestVC._isEnabled = self._config['vc']['isEnabled']

    def test_0001_list_vc(self):
        """Platform.list_vcenters prints a list of virtual center servers."""
        logger = Environment.get_default_logger()
        platform = Platform(TestVC._client)
        vcenters = platform.list_vcenters()
        for vcenter in vcenters:
            logger.debug('vCenter found: %s' % vcenter.get('name'))
        self.assertTrue(len(vcenters) > 0)

    def test_0002_get_vc(self):
        """Platform.get_vcenter finds a known vcenter."""
        logger = Environment.get_default_logger()
        platform = Platform(TestVC._client)
        vcenter = platform.get_vcenter(TestVC._vcenter_host_name)
        logger.debug('vCenter: name=%s, url=%s' %
                     (vcenter.get('name'), vcenter.Url.text))
        self.assertIsNotNone(vcenter)

    def test_0003_get_vc_negative(self):
        """Platform.get_vcenter does not find a non-existent vcenter."""
        try:
            platform = Platform(TestVC._client)
            platform.get_vcenter(TestVC._vcenter_invalid)
            self.assertFalse(False)
        except Exception as e:
            self.assertIn('not found', str(e).lower())

    def test_0004_attach_vc(self):
        """Platform.attach_vcenter attaches a vcenter."""
        platform = Platform(TestVC._client)

        vc = platform.attach_vcenter(
            vc_server_name=TestVC._vcServerName,
            vc_server_host=TestVC._vcServerHost,
            vc_admin_user=TestVC._vcAdminUser,
            vc_admin_pwd=TestVC._vcAdminPwd,
            nsx_server_name=TestVC._NSXServerName,
            nsx_host=TestVC._NSXHost,
            nsx_admin_user=TestVC._NSXAdminUser,
            nsx_admin_pwd=TestVC._NSXAdminPwd,
            is_enabled=TestVC._isEnabled)
        task = vc.VimServer['{' + NSMAP['vcloud'] + '}Tasks'].Task[0]
        TestVC._client.get_task_monitor().wait_for_success(task=task)
        self.assertEqual(TestVC._vcServerName, vc.VimServer.get('name'))

    def test_0005_enable_vc(self):
        """Platform.enable_vcenter enables a vcenter.

        Wait for async command to complete before checking result.
        """
        platform = Platform(TestVC._client)

        task = platform.enable_disable_vcenter(
            vc_name=TestVC._vcServerName, enable_flag=True)
        TestVC._client.get_task_monitor().wait_for_success(task=task)
        vc = platform.get_vcenter(name=TestVC._vcServerName)
        self.assertTrue(vc.IsEnabled)

    def test_0006_disable_vc(self):
        """Platform.disable_vcenter disables a vcenter.

        Wait for async command to complete before checking result.
        """
        platform = Platform(TestVC._client)

        task = platform.enable_disable_vcenter(
            vc_name=TestVC._vcServerName, enable_flag=False)
        TestVC._client.get_task_monitor().wait_for_success(task=task)
        vc = platform.get_vcenter(name=TestVC._vcServerName)
        self.assertFalse(vc.IsEnabled)

    def test_0007_detach_vc(self):
        """Platform.detach_vcenter disables a vcenter.

        Wait for async command to complete before checking result.
        """
        try:
            platform = Platform(TestVC._client)

            task = platform.detach_vcenter(
                vc_name=TestVC._vcServerName)
            TestVC._client.get_task_monitor().wait_for_success(task=task)
            platform.get_vcenter(name=TestVC._vcServerName)
            self.assertFalse(False)
        except Exception as e:
            self.assertIn('not found', str(e).lower())

    def test_9999_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestVC._client.logout()


if __name__ == '__main__':
    unittest.main()
