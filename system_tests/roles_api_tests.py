# VMware vCloud Director Python SDK
# Copyright (c) 2021 VMware, Inc. All Rights Reserved.
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

from vcloud.rest.openapi.apis.roles_api import RolesApi
from vcloud.rest.openapi.models.role import Role
from vcloud.rest.openapi.models.roles import Roles

from pyvcloud.system_test_framework.api_base_test import ApiBaseTestCase
from pyvcloud.vcd.vcd_client import VcdClient, QueryParamsBuilder


class TestApiClient(ApiBaseTestCase):
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

    _test_role_name = 'test_role' + str(uuid1())
    _test_role_desc = 'Test role created by Python API client'
    _role = None

    def test_0050_create_role(self):
        """Create a role using generated model class.
        This test passes if the role is created successfully and details of
        the role are correct.
        """
        self.assertIsNotNone(TestApiClient._client, msg="Login Failed or was not performed")
        role_model = Role(name=TestApiClient._test_role_name,
                          description=TestApiClient._test_role_desc)

        TestApiClient._logger.debug('Creating a role with name %s',
                                    TestApiClient._test_role_name)

        role_api = RolesApi(api_client=TestApiClient._client)
        role = role_api.create_role(role_model)
        self.assertIsNotNone(role)
        self.assertEqual(role.name, TestApiClient._test_role_name)
        self.assertEqual(role.description, TestApiClient._test_role_desc)
        TestApiClient._role = role

    def test_0060_update_role(self):
        """Update a role.
        Finds edit link by rel and model, then updates the org.
        This test passes if the returned role is not None and the modified
        property is updated.
        """
        self.assertIsNotNone(TestApiClient._client, msg="Login Failed or was not performed")
        self.assertIsNotNone(TestApiClient._role, 'Role not created')

        new_desc = "Updated " + TestApiClient._test_role_desc
        TestApiClient._role.description = new_desc

        TestApiClient._logger.debug('Updating role %s',
                                    TestApiClient._test_role_name)
        role_api = RolesApi(api_client=TestApiClient._client)
        role = role_api.update_role(updated_role=TestApiClient._role, id=TestApiClient._role.id)
        self.assertIsNotNone(role)
        self.assertEqual(role.description, new_desc)
        TestApiClient._role = role

    def test_0070_query_role(self):
        """Query a role.
        Queries a role by name filter.
        This test passes if the query result consists exactly one record.
        """
        self.assertIsNotNone(TestApiClient._client, msg="Login Failed or was not performed")
        self.assertIsNotNone(TestApiClient._role, 'Role not created')
        name_filter = 'name==%s' % TestApiClient._test_role_name
        query_params = QueryParamsBuilder().set_filter(name_filter).set_page(
            1).set_page_size(5).set_sort_asc('name').build()

        query_uri = '/1.0.0/roles'

        TestApiClient._logger.debug('Executing query on %s with params %s' %
                                    (query_uri, query_params))
        roles = TestApiClient._client.call_api(method='GET',
                                               resource_path=query_uri,
                                               query_params=query_params,
                                               response_type=Roles,
                                               header_params=TestApiClient._client.default_headers)
        self.assertEqual(len(roles.values), 1)

    def test_0080_delete_role(self):
        """Delete a role.
        This test passes if the returned status code is 204.
        """
        self.assertIsNotNone(TestApiClient._client, msg="Login Failed or was not performed")
        self.assertIsNotNone(TestApiClient._role, 'Role not created')
        role_api = RolesApi(api_client=TestApiClient._client)

        TestApiClient._logger.debug('Deleting role %s',
                                    TestApiClient._test_role_name)
        role_api.delete_role(id=TestApiClient._role.id)
        self.assertEqual(TestApiClient._client.get_last_status(), 204)


if __name__ == '__main__':
    unittest.main()
