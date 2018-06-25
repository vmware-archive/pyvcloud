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


class TestSearch(BaseTestCase):
    """Test pyvcloud search functions."""

    def setUp(self):
        """Store list of result formats and init client variable."""
        self._result_formats = [r for r in QueryResultFormat]
        self._client = None

    def tearDown(self):
        """Log out client connection if allocated."""
        if self._client is not None:
            self._client.logout()

    def test_0010_find_existing_with_admin(self):
        """Find entities with admin account with optional filter parameters."""
        # Get admin client.  This will not be logged out to avoid messing
        # up Environment class.
        admin_client = None
        try:
            admin_client = Environment.get_sys_admin_client()
            resource_type_cc = 'organization'
            # Fetch all orgs.
            q1 = admin_client.get_typed_query(
                resource_type_cc,
                query_result_format=QueryResultFormat.ID_RECORDS,
                qfilter=None)
            q1_records = list(q1.execute())
            self.assertTrue(
                len(q1_records) > 0,
                msg="Find at least one organization")
            name0 = q1_records[0].get('name')

            # Find the org again using an equality filter.
            eq_filter = ('name', name0)
            q2 = admin_client.get_typed_query(
                resource_type_cc,
                query_result_format=QueryResultFormat.ID_RECORDS,
                equality_filter=eq_filter)
            q2_records = list(q2.execute())
            self.assertEqual(
                1, len(q2_records),
                msg="Find org with equality filter")

            # Find the org again using a query filter string
            q3 = admin_client.get_typed_query(
                resource_type_cc,
                query_result_format=QueryResultFormat.ID_RECORDS,
                qfilter="name=={0}".format(name0))
            q3_records = list(q3.execute())
            self.assertEqual(1, len(q3_records),
                             msg="Find org with query filter")
        finally:
            if admin_client is not None:
                admin_client.logout()

    def test_0020_find_existing_entities_with_org_user(self):
        """Find entities with low-privilege org user."""
        self._client = Environment.get_client_in_default_org(
            CommonRoles.CATALOG_AUTHOR)
        q1 = self._client.get_typed_query(
            ResourceType.CATALOG.value,
            query_result_format=QueryResultFormat.ID_RECORDS)
        q1_records = list(q1.execute())
        self.assertTrue(len(q1_records) > 0,
                        msg="Find at least one catalog item")

    def test_0030_find_non_existing(self):
        """Verify we return nothing if no entities exist."""
        self._client = Environment.get_client_in_default_org(
            CommonRoles.VAPP_USER)
        for format in self._result_formats:
            # Use the generator directly.
            q1 = self._client.get_typed_query(
                ResourceType.ORGANIZATION.value,
                query_result_format=QueryResultFormat.ID_RECORDS)
            count = 0
            for item in q1.execute():
                count += 1
            self.assertEqual(0, count, "Should not find orgs via generator")
            # Try a list.
            q1_records = list(q1.execute())
            self.assertEqual(
                0, len(q1_records),
                "Should not find any orgs via list")

    def test_0040_check_all_resource_types(self):
        """Verify that we can search on any resource type without error."""
        self._client = Environment.get_client_in_default_org(
            CommonRoles.ORGANIZATION_ADMINISTRATOR)
        resource_types = [r.value for r in ResourceType]
        # Some types of course won't exist but the search should not fail.
        for resource_type in resource_types:
            q1 = self._client.get_typed_query(
                resource_type,
                query_result_format=QueryResultFormat.ID_RECORDS)
            q1_records = list(q1.execute())
            self.assertTrue(
                len(q1_records) >= 0,
                "Should get a list, even if tempty")

    def test_0050_check_result_formats(self):
        """Verify we get expected results for all result formats."""
        self._client = Environment.get_client_in_default_org(
            CommonRoles.ORGANIZATION_ADMINISTRATOR)
        for format in self._result_formats:
            # Ensure format works with generator.
            q1 = self._client.get_typed_query(
                ResourceType.USER.value,
                query_result_format=format)
            count = 0
            for result in q1.execute():
                count += 1
            self.assertTrue(
                count >= 4,
                "Expect at least 4 users from generator: {0}".format(format))

            # Ensure format works with list built over generator.
            q2 = self._client.get_typed_query(
                ResourceType.USER.value,
                query_result_format=format)
            q2_result = list(q2.execute())
            self.assertTrue(
                len(q2_result) >= 4,
                "Expect at least 4 users from list: {0}".format(format))


if __name__ == '__main__':
    unittest.main()
