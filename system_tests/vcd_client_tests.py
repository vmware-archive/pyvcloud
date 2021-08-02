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

from vcloud.rest.openapi.apis.sessions_api import SessionsApi

from pyvcloud.system_test_framework.base_test import BaseTestCase
from pyvcloud.system_test_framework.environment import Environment
from pyvcloud.vcd.vcd_client import VcdClient, BasicLoginCredentials


class TestApiClient(BaseTestCase):
    """Test API client module functions.
    Test cases in this module have ordering dependencies.
    """

    # Test configuration parameters and logger for output.
    _host = None
    _user = None
    _pass = None
    _logger = None

    # Client to be used by all tests.
    _client = None

    _session = None

    def test_0000_setup(self):
        """Setup a API client for other tests in this module.
        Create a API client as per test configurations.
        This test passes if the client in not None.
        """
        TestApiClient._logger = Environment.get_default_logger()
        TestApiClient._client = TestApiClient._create_client_with_credentials()
        self.assertIsNotNone(TestApiClient._client)

    def test_0010_get_current_session(self):
        """Get session using generated model class.
        This test passes if the session is fetched successfully.
        """
        session_api = SessionsApi(api_client=TestApiClient._client)
        session = session_api.get_current_session()
        self.assertIsNotNone(session, msg="Failed to fetch session")
        TestApiClient._session = session
        TestApiClient._client = session_api.api_client

    def test_0020_delete_session(self):
        """Deletes current session.
        This test passes if the returned status code is 204.
        """
        self.assertIsNotNone(TestApiClient._session, msg="Previous TestCase to fetch session FAILED, "
                                                         "so cannot perform delete operation")
        session_api = SessionsApi(api_client=TestApiClient._client)
        session = session_api.logout(id=TestApiClient._session.id)
        self.assertEqual(TestApiClient._client.get_last_status(), 204)
        TestApiClient._session = session

    def test_9999_cleanup(self):
        """Log out client connection if allocated."""
        if TestApiClient._client is not None and TestApiClient._client._session:
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
        api_version = config['vcd']['api_version']
        client = VcdClient(host,
                           api_version=api_version,
                           verify_ssl_certs=False,
                           log_requests=True,
                           log_bodies=True,
                           log_headers=True)
        creds = BasicLoginCredentials(user, org, pwd)
        client.set_credentials(creds)
        return client


if __name__ == '__main__':
    unittest.main()
