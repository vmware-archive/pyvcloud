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
from pyvcloud.system_test_framework.environment import CommonRoles
from pyvcloud.system_test_framework.environment import developerModeAware
from pyvcloud.system_test_framework.environment import Environment
from pyvcloud.vcd.platform import Platform
from pyvcloud.vcd.utils import to_dict


class TestNSXT(BaseTestCase):

    def test_000_setup(self):
        TestNSXT._client = Environment.get_sys_admin_client()

    def test_010_register_nsxt(self):
        platform = Platform(TestNSXT._client)

        nsxt = platform.register_nsxt_manager(
            nsxt_manager_name=Environment._config['nsxt']['manager_name'],
            nsxt_manager_url=Environment._config['nsxt']['manager_host_url'],
            nsxt_manager_username=Environment._config['nsxt']['admin_user'],
            nsxt_manager_password=Environment._config['nsxt']['admin_pwd'],
            nsxt_manager_description=Environment._config['nsxt']['description'])
        assert Environment._config['nsxt']['manager_name'] == nsxt.get('name')

    def test_030_unregister_nsxt(self):
        platform = Platform(TestNSXT._client)

        platform.unregister_nsxt_manager(
            nsxt_manager_name=Environment._config['nsxt']['manager_name'])

    def test_020_list_nsxt_managers(self):
        platform = Platform(TestNSXT._client)

        query = platform.list_nsxt_managers()
        result = []
        for record in list(query):
            result.append(
                to_dict(
                    record,
                    exclude=['href']))
        print(result)


if __name__ == '__main__':
    unittest.main()
