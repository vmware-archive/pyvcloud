# VMware vCloud Director Python SDK
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
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

from vcloud.api.rest.schema_v1_5.admin_org_type import AdminOrgType

from vcloud.rest.openapi.apis.org_api import OrgApi
from vcloud.rest.openapi.models.org import Org

from pyvcloud.system_test_framework.base_test import BaseTestCase
from pyvcloud.system_test_framework.environment import Environment
from pyvcloud.vcd.vcd_client import VcdClient
from pyvcloud.vcd.client import BasicLoginCredentials


class TestApiClient(BaseTestCase):
    """Test API client module functions.
    Test cases in this module have ordering dependencies.
    """

    # Test configuration parameters and logger for output.
    _config = None
    _host = None
    _user = None
    _pass = None

    _logger = None

    # Client to be used by all tests.
    _client = None

    _test_org_name = 'test_org_' + str(uuid1())
    _test_org_desc = 'Test org created by Python API client'
    _test_display_name = 'Test Full Name'
    _org = None

    ADMIN_ORG_MEDIA_TYPE = 'application/vnd.vmware.admin.organization+json'

    def test_0000_setup(self):
        """Setup a API client for other tests in this module.
        Create a API client as per test configurations.
        This test passes if the client in not None.
        """
        TestApiClient._logger = Environment.get_default_logger()
        TestApiClient._client = TestApiClient._create_client_with_credentials()
        self.assertIsNotNone(TestApiClient._client)

    def test_0010_create_org(self):
        """Create an org using generated model class.
        This test passes if the org is created successfully and details of
        the organization are correct.
        """
        org_model = Org(name=TestApiClient._test_org_name,
                        display_name=TestApiClient._test_display_name,
                        is_enabled=True)

        org_api = OrgApi(api_client=TestApiClient._client)
        org = org_api.create_org(org_model)

        self.assertIsNotNone(org, msg="Failed to create organization")
        self.assertEqual(org.name, TestApiClient._test_org_name)
        self.assertTrue(org.is_enabled, msg="Organization created name is incorrect")
        TestApiClient._org = org

    def test_0020_update_org(self):
        """Update an org.
        Finds edit link by rel and type and updates the org.
        This test passses if the retuned org is not None and the modified
        property is updated.
        """
        self.assertIsNotNone(TestApiClient._org, msg="Previous TestCase to create organization FAILED, "
                                                     "so cannot perform update operation")

        TestApiClient._logger.debug('Updating org %s',
                                    TestApiClient._test_org_name)
        org_api = OrgApi(api_client=TestApiClient._client)

        TestApiClient._org.is_enabled = False
        org_urn = TestApiClient._org.id

        org = org_api.update_org(modified_org=TestApiClient._org, org_urn=org_urn)

        self.assertIsNotNone(org, msg="Failed to update organization")
        self.assertFalse(org.is_enabled, msg="Organization %s is not disabled" % TestApiClient._org.name)
        TestApiClient._org = org

    def test_0030_query_org(self):
        """Query an org.
        Queries an org by type and name filter.
        This test passes if the query result consists exactly one record.
        """
        self.assertIsNotNone(TestApiClient._org, msg="Previous TestCase to create organization FAILED, "
                                                     "so cannot perform query operation")

        name_filter = 'name==%s' % TestApiClient._test_org_name
        page_no = 1
        page_size = 5

        TestApiClient._logger.debug('Executing query on orgs with params page=%s, '
                                    'page_size=%s, filter=%s' % (page_no, page_size, name_filter))

        org_api = OrgApi(api_client=TestApiClient._client)
        result = org_api.query_orgs(page=page_no, page_size=page_size, filter=name_filter)
        self.assertEqual(result.result_total, 1)
        self.assertEqual(result.values[0].id, TestApiClient._org.id)

    def test_0040_delete_org(self):
        """Delete an org.
        This test passes if task is success
        """
        self.assertIsNotNone(TestApiClient._org, msg="Previous TestCase to create organization FAILED, "
                                                     "so cannot perform delete org operation")

        TestApiClient._logger.debug('Deleting %s',
                                    TestApiClient._test_org_name)

        org_urn = TestApiClient._org.id

        org_api = OrgApi(api_client=TestApiClient._client)

        org_api.delete_org(org_urn=org_urn)
        TestApiClient._client.wait_for_last_task()

    def test_9999_cleanup(self):
        """Log out client connection if allocated."""
        if TestApiClient._client is not None:
            try:
                TestApiClient._logger.info("Logging out client automatically")
                TestApiClient._client.logout()
            except Exception:
                TestApiClient._logger.warning("Client logout failed",
                                              exc_info=True)

    @classmethod
    def _create_client_with_credentials(cls):
        """Create client and login."""
        config = Environment.get_config()
        host = config['vcd']['host']
        org = config['vcd']['sys_org_name']
        user = config['vcd']['sys_admin_username']
        pwd = config['vcd']['sys_admin_pass']
        client = VcdClient(host,
                           verify_ssl_certs=False,
                           log_requests=True,
                           log_bodies=True,
                           log_headers=True)
        creds = BasicLoginCredentials(user, org, pwd)
        client.set_credentials(creds)
        return client


if __name__ == '__main__':
    unittest.main()
