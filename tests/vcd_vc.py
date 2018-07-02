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

import time
import unittest

from pyvcloud.vcd.platform import Platform
from pyvcloud.vcd.test import TestCase


class TestVC(TestCase):

    def test_0001_list_vc(self):
        platform = Platform(self.client)
        vcenters = platform.list_vcenters()
        for vcenter in vcenters:
            self.logger.debug('vCenter found: %s' % vcenter.get('name'))
            print('vCenter found: %s' % vcenter.get('name'))
        assert len(vcenters) > 0
        """No unit test for list_vc."""

    def test_0002_get_vc(self):
        """Platform.get_vcenter finds a known vcenter."""
        platform = Platform(self.client)
        vcenter = platform.get_vcenter(self.config['vcd']['vcServerName'])
        self.logger.debug('vCenter: name=%s, url=%s' %
                          (vcenter.get('name'), vcenter.Url.text))
        assert vcenter is not None

    def test_0003_get_vc_negative(self):
        """Platform.get_vcenter does not find a non-existent vcenter."""
        try:
            platform = Platform(self.client)
            platform.get_vcenter(self.config['vcd']['vcenter_invalid'])
            assert False
        except Exception as e:
            assert 'not found' in str(e).lower()

    def test_0004_attach_vc(self):
        """Platform.attach_vcenter attaches a vcenter."""
        platform = Platform(self.client)

        vc = platform.attach_vcenter(
            vc_server_name=self.config['vcd']['vcServerName'],
            vc_server_host=self.config['vcd']['vcServerHost'],
            vc_admin_user=self.config['vcd']['vcAdminUser'],
            vc_admin_pwd=self.config['vcd']['vcAdminPwd'],
            nsx_server_name=self.config['vcd']['NSXServerName'],
            nsx_host=self.config['vcd']['NSXHost'],
            nsx_admin_user=self.config['vcd']['NSXAdminUser'],
            nsx_admin_pwd=self.config['vcd']['NSXAdminPwd'],
            is_enabled=self.config['vcd']['isEnabled'])
        assert self.config['vcd']['vcServerName'] == vc.VimServer.get('name')

    def test_0005_enable_vc(self):
        """Platform.enable_vcenter enables a vcenter.

        Sleep(5) to wait for async command to complete before checking result.
        """
        platform = Platform(self.client)

        platform.\
            enable_disable_vcenter(vc_name=self.config['vcd']['vcServerName'],
                                   enable_flag=True)
        time.sleep(5)
        vc = platform.get_vcenter(name=self.config['vcd']['vcServerName'])
        assert vc.IsEnabled

    def test_0006_disable_vc(self):
        """Platform.disable_vcenter disables a vcenter.

        Sleep(5) to wait for async command to complete before checking result.
        """
        platform = Platform(self.client)

        platform.\
            enable_disable_vcenter(vc_name=self.config['vcd']['vcServerName'],
                                   enable_flag=False)
        time.sleep(5)
        vc = platform.get_vcenter(name=self.config['vcd']['vcServerName'])
        assert not vc.IsEnabled

    def test_0007_detach_vc(self):
        """Platform.detach_vcenter disables a vcenter.

        Sleep(5) to wait for async command to complete before checking result.
        """
        try:
            platform = Platform(self.client)

            platform.detach_vcenter(vc_name=self.config['vcd']['vcServerName'])
            time.sleep(5)
            platform.get_vcenter(name=self.config['vcd']['vcServerName'])
            assert False
        except Exception as e:
            assert 'not found' in str(e).lower()


if __name__ == '__main__':
    unittest.main()
