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
from vcloud.api.rest.schema_v1_5.query_result_records_type import \
    QueryResultRecordsType
from vcloud.api.rest.schema_v1_5.task_type import TaskType
from vcloud.rest.openapi.models.role import Role
from vcloud.rest.openapi.models.roles import Roles

from pyvcloud.system_test_framework.base_test import BaseTestCase
from pyvcloud.system_test_framework.environment import Environment
from pyvcloud.vcd.api_client import ApiClient, QueryParamsBuilder
from pyvcloud.vcd.client import BasicLoginCredentials


class TestApiClient(BaseTestCase):
    """Test API client module functions.

    Test cases in this module have ordering dependencies.
    """

    # Test configuration parameters and logger for output.
    _config = None
    _host = None
    _org = None
    _user = None
    _pass = None

    _logger = None

    # Client to be used by all tests.
    _client = None

    ADMIN_ORG_MEDIA_TYPE = 'application/vnd.vmware.admin.organization+json'
    OPEN_API_MEDIA_TYPE = 'application/json'

    _test_org_name = 'test_org_' + str(uuid1())
    _test_org_desc = 'Test org created by Python API client'
    _org = None

    _test_role_name = 'test_role' + str(uuid1())
    _test_role_desc = 'Test role created by Python API client'
    _role = None

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
        org_model = AdminOrgType()
        org_model.name = TestApiClient._test_org_name
        org_model.full_name = TestApiClient._test_org_name
        org_model.is_enabled = True
        org_model.description = TestApiClient._test_org_desc
        org_model.settings = {}

        TestApiClient._logger.debug('Creating an org with name %s',
                                    TestApiClient._test_org_name)
        org = TestApiClient._client.call_api(
            method='POST',
            uri=TestApiClient._client.build_api_uri('/admin/orgs'),
            contents=org_model,
            media_type=TestApiClient.ADMIN_ORG_MEDIA_TYPE,
            response_type=AdminOrgType)
        self.assertIsNotNone(org)
        self.assertEqual(org.name, TestApiClient._test_org_name)
        self.assertEqual(org.full_name, TestApiClient._test_org_name)
        self.assertTrue(org.is_enabled)
        TestApiClient._org = org

    def test_0020_update_org(self):
        """Update an org.

        Finds edit link by rel and type and updates the org.

        This test passses if the retuned org is not None and the modified
        property is updated.
        """
        edit_link = TestApiClient._client.find_first_link(
            rel='edit', type=TestApiClient.ADMIN_ORG_MEDIA_TYPE)
        self.assertIsNotNone(edit_link, 'Edit link not found')

        TestApiClient._logger.debug('Updating org %s',
                                    TestApiClient._test_org_name)
        TestApiClient._org.is_enabled = False
        org = TestApiClient._client.call_api(
            method='PUT',
            uri=edit_link.href,
            contents=TestApiClient._org,
            media_type=TestApiClient.ADMIN_ORG_MEDIA_TYPE,
            response_type=AdminOrgType)
        self.assertIsNotNone(org)
        self.assertFalse(org.is_enabled)
        TestApiClient._org = org

    def test_0030_query_org(self):
        """Query an org.

        Queries an org by type and name filter.

        This test passes if the query result consists exactly one record.
        """
        name_filter = 'name==%s' % TestApiClient._test_org_name
        query_params = QueryParamsBuilder().set_type(
            'organization').set_format(
                QueryParamsBuilder.RECORDS).set_filter(name_filter).set_page(
                    1).set_page_size(5).set_sort_asc('name').build()
        query_uri = TestApiClient._client.build_api_uri('/query')

        TestApiClient._logger.debug('Executing query on %s with params %s' %
                                    (query_uri, query_params))
        result = TestApiClient._client.call_api(
            method='GET',
            uri=query_uri,
            params=query_params,
            response_type=QueryResultRecordsType)
        self.assertEqual(len(result.record), 1)

    def test_0040_delete_org(self):
        """Delete an org.

        This test passes if the returned status code is 204.
        """
        TestApiClient._logger.debug('Deleting %s',
                                    TestApiClient._test_org_name)

        TestApiClient._client.call_api(method='DELETE',
                                       uri=TestApiClient._org.href,
                                       response_type=TaskType)
        self.assertEqual(TestApiClient._client.get_last_status(), 202)
        TestApiClient._client.wait_for_last_task()

    def test_0050_create_role(self):
        """Create a role using generated model class.

        This test passes if the role is created successfully and details of
        the role are correct.
        """
        role_model = Role(name=TestApiClient._test_role_name,
                          description=TestApiClient._test_role_desc)

        TestApiClient._logger.debug('Creating a role with name %s',
                                    TestApiClient._test_role_name)
        role = TestApiClient._client.call_api(
            method='POST',
            uri=TestApiClient._client.build_cloudapi_uri('/1.0.0/roles'),
            contents=role_model,
            media_type=TestApiClient.OPEN_API_MEDIA_TYPE,
            response_type=Role)
        self.assertIsNotNone(role)
        self.assertEqual(role.name, TestApiClient._test_role_name)
        self.assertEqual(role.description, TestApiClient._test_role_desc)
        TestApiClient._role = role

    def test_0060_update_role(self):
        """Update a role.

        Finds edit link by rel and model, then updates the org.

        This test passses if the retuned role is not None and the modified
        property is updated.
        """
        edit_link = TestApiClient._client.find_first_link(rel='edit',
                                                          model='Role')
        self.assertIsNotNone(edit_link, 'Edit link not found')

        new_desc = "Updated " + TestApiClient._test_role_desc
        TestApiClient._role.description = new_desc

        TestApiClient._logger.debug('Updating role %s',
                                    TestApiClient._test_role_name)
        role = TestApiClient._client.call_api(
            method='PUT',
            uri=edit_link.href,
            contents=TestApiClient._role,
            media_type=TestApiClient.OPEN_API_MEDIA_TYPE,
            response_type=Role)
        self.assertIsNotNone(role)
        self.assertEqual(role.description, new_desc)
        TestApiClient._role = role

    def test_0070_query_role(self):
        """Query a role.

        Queries a role by name filter.

        This test passes if the query result consists exactly one record.
        """
        name_filter = 'name==%s' % TestApiClient._test_role_name
        query_params = QueryParamsBuilder().set_filter(name_filter).set_page(
            1).set_page_size(5).set_sort_asc('name').build()
        query_uri = TestApiClient._client.build_cloudapi_uri('/1.0.0/roles')

        TestApiClient._logger.debug('Executing query on %s with params %s' %
                                    (query_uri, query_params))
        roles = TestApiClient._client.call_api(method='GET',
                                               uri=query_uri,
                                               params=query_params,
                                               response_type=Roles)
        self.assertEqual(len(roles.values), 1)

    def test_0080_delete_role(self):
        """Delete a role.

        This test passes if the returned status code is 204.
        """
        remove_link = TestApiClient._client.find_first_link(rel='remove',
                                                            model='Role')
        self.assertIsNotNone(remove_link, 'Remove link not found')

        TestApiClient._logger.debug('Deleting role %s',
                                    TestApiClient._test_role_name)
        TestApiClient._client.call_api(method='DELETE', uri=remove_link.href)
        self.assertEqual(TestApiClient._client.get_last_status(), 204)

    def test_9999_cleanup(self):
        """Log out client connection if allocated."""
        if TestApiClient._client is not None:
            try:
                TestApiClient._logger.debug("Logging out client automatically")
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
        client = ApiClient(host,
                           verify_ssl_certs=False,
                           log_requests=True,
                           log_bodies=True,
                           log_headers=True)
        creds = BasicLoginCredentials(user, org, pwd)
        client.set_credentials(creds)
        return client


if __name__ == '__main__':
    unittest.main()
