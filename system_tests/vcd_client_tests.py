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

from pyvcloud.system_test_framework.api_base_test import ApiBaseTestCase


class TestApiClient(ApiBaseTestCase):
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

if __name__ == '__main__':
    unittest.main()
