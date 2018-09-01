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

from pyvcloud.vcd.platform import Platform


class TestPVDC(BaseTestCase):

    def test_0000_setup(self):
        # TODO(): need more pipeline work before this test can actually be run
        TestPVDC._client = Environment.get_sys_admin_client()
        TestPVDC._config = Environment.get_config()
        TestPVDC._vcenter_host_name = self._config['vc']['vcenter_host_name']
        TestPVDC._pvdc_name = self._config['pvdc']['pvdc_name']
        TestPVDC._resource_pool_names = \
            self._config['pvdc']['resource_pool_names']

    def test_0010_attach_resource_pools(self):
        """Attach resource pool(s) to a PVDC."""
        platform = Platform(TestPVDC._client)
        task = platform.attach_resource_pools_to_provider_vdc(
            TestPVDC._pvdc_name,
            TestPVDC._resource_pool_names)
        TestPVDC._client.get_task_monitor().wait_for_success(task=task)

    def test_0020_detach_resource_pools(self):
        """Disable and delete resource pool(s) from a PVDC."""
        platform = Platform(TestPVDC._client)
        task = platform.detach_resource_pools_from_provider_vdc(
            TestPVDC._pvdc_name,
            TestPVDC._resource_pool_names)
        TestPVDC._client.get_task_monitor().wait_for_success(task=task)

    def test_9999_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestPVDC._client.logout()


if __name__ == '__main__':
    unittest.main()
