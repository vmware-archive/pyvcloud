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
import urllib.parse

from pyvcloud.system_test_framework.base_test import BaseTestCase
from pyvcloud.system_test_framework.environment import Environment

from pyvcloud.vcd.client import QueryResultFormat
from pyvcloud.vcd.client import ResourceType
from pyvcloud.vcd.platform import Platform


class TestNSXT(BaseTestCase):

    def test_0000_setup(self):
        TestNSXT._client = Environment.get_sys_admin_client()

    def test_0010_register_nsxt(self):
        """Client can register a new NSX-T mgr if none exists w/ same name."""
        platform = Platform(TestNSXT._client)

        manager_name = Environment._config['nsxt']['manager_name']
        query_filter = 'name==%s' % urllib.parse.quote_plus(manager_name)
        query = TestNSXT._client.get_typed_query(
            ResourceType.NSXT_MANAGER.value,
            query_result_format=QueryResultFormat.REFERENCES,
            qfilter=query_filter)
        records = list(query.execute())
        if len(records) > 0:
            platform.unregister_nsxt_manager(nsxt_manager_name=manager_name)

        nsxt = platform.register_nsxt_manager(
            nsxt_manager_name=manager_name,
            nsxt_manager_url=Environment._config['nsxt']['manager_host_url'],
            nsxt_manager_username=Environment._config['nsxt']['admin_user'],
            nsxt_manager_password=Environment._config['nsxt']['admin_pwd'],
            nsxt_manager_description=Environment._config['nsxt']['descrip'])
        assert Environment._config['nsxt']['manager_name'] == nsxt.get('name')

    def test_0020_list_nsxt_managers(self):
        """Client can list NSX-T mgrs that have been registered."""
        platform = Platform(TestNSXT._client)

        manager_name = Environment._config['nsxt']['manager_name']

        query = platform.list_nsxt_managers()
        result = []
        for record in list(query):
            result.append(record.get('name'))

        self.assertIn(manager_name, result)

    def test_0030_unregister_nsxt(self):
        """Client can unregister an NSX-T mgr."""
        platform = Platform(TestNSXT._client)

        manager_name = Environment._config['nsxt']['manager_name']
        platform.unregister_nsxt_manager(nsxt_manager_name=manager_name)

        query_filter = 'name==%s' % urllib.parse.quote_plus(manager_name)
        query = TestNSXT._client.get_typed_query(
            ResourceType.NSXT_MANAGER.value,
            query_result_format=QueryResultFormat.REFERENCES,
            qfilter=query_filter)
        records = list(query.execute())
        self.assertTrue(len(records) == 0)

    def test_9999_setup(self):
        """Release all resources held by this object for testing purposes."""
        TestNSXT._client.logout()


if __name__ == '__main__':
    unittest.main()
