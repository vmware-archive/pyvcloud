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
from pyvcloud.system_test_framework.environment import Environment

from pyvcloud.vcd.client import QueryResultFormat
from pyvcloud.vcd.client import ResourceType
from pyvcloud.vcd.client import RESOURCE_TYPES
from pyvcloud.vcd.utils import to_dict


class TestSearch(BaseTestCase):
    """Test pyvcloud search functions"""
    _client = None
    _vdc = None

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_0010_find_existing_with_admin(self):
        """Find entities with admin account with optional filter parameters"""
        resource_type_cc = 'organization'
        client = Environment.get_sys_admin_client()
        # Fetch all orgs.
        q1 = client.get_typed_query(
            resource_type_cc,
            query_result_format=QueryResultFormat.ID_RECORDS,
            qfilter=None)
        q1_records = list(q1.execute())
        self.assertTrue(
            len(q1_records) > 0,
            msg="Find at least one organization")
        for r in q1_records:
            r_dict = to_dict(r, resource_type=resource_type_cc)
            name0 = r_dict['name']
            break

        # Find the org again using an equality filter.
        eq_filter = ('name', name0)
        q2 = client.get_typed_query(
            resource_type_cc,
            query_result_format=QueryResultFormat.ID_RECORDS,
            equality_filter=eq_filter)
        q2_records = list(q2.execute())
        self.assertEqual(
            1, len(q2_records),
            msg="Find org with equality filter")

        # Find the org again using a query filter string
        q3 = client.get_typed_query(
            resource_type_cc,
            query_result_format=QueryResultFormat.ID_RECORDS,
            qfilter="name=={0}".format(name0))
        q3_records = list(q3.execute())
        self.assertEqual(1, len(q3_records), msg="Find org with query filter")

    def test_0020_find_existing_with_org_user(self):
        """Find entities with low-privilege org user"""
        client = Environment.get_client_in_default_org(
            CommonRoles.CATALOG_AUTHOR)
        q1 = client.get_typed_query(
            ResourceType.CATALOG.value,
            query_result_format=QueryResultFormat.ID_RECORDS)
        q1_records = list(q1.execute())
        self.assertTrue(len(q1_records) > 0,
                        msg="Find at least one catalog item")

    def test_0030_find_non_existing(self):
        """Verify that we return nothing if no entities exist"""
        client = Environment.get_client_in_default_org(CommonRoles.VAPP_USER)
        q1 = client.get_typed_query(
            ResourceType.ORGANIZATION.value,
            query_result_format=QueryResultFormat.ID_RECORDS)
        q1_records = list(q1.execute())
        self.assertTrue(len(q1_records) == 0, "Should not find any orgs")

    def test_0040_check_all_resource_types(self):
        """Loop through all resource types to prove we can search on them"""
        client = Environment.get_client_in_default_org(
            CommonRoles.ORGANIZATION_ADMINISTRATOR)
        for resource_type in RESOURCE_TYPES:
            q1 = client.get_typed_query(
                resource_type,
                query_result_format=QueryResultFormat.ID_RECORDS)
            q1_records = list(q1.execute())
            self.assertTrue(len(q1_records) >= 0, "Should get a list")

if __name__ == '__main__':
    unittest.main()
