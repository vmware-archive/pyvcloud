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

import pyvcloud.vcd.client as client
from pyvcloud.vcd.exceptions import VcdException


class TestClient(BaseTestCase):
    """Test pyvcloud client module functions.

    Test cases in this module do not have ordering dependencies, hence all
    setup is accomplished using Python unittest setUp and tearDown methods.
    """

    # Test configuration parameters and logger for output.
    _config = None
    _host = None
    _org = None
    _user = None
    _pass = None

    _logger = None

    # Temporary client, logged out if found.
    _client = None

    def setUp(self):
        self._config = Environment.get_config()
        self._host = self._config['vcd']['host']
        self._org = self._config['vcd']['sys_org_name']
        self._user = self._config['vcd']['sys_admin_username']
        self._pass = self._config['vcd']['sys_admin_pass']

        self._logger = Environment.get_default_logger()

    def tearDown(self):
        """Log out client connection if allocated."""
        if self._client is not None:
            try:
                self._logger.debug("Logging out client automatically")
                self._client.logout()
            except Exception:
                self._logger.warning("Client logout failed", exc_info=True)

    def test_0010_use_default_api_version(self):
        """Client defaults to highest server API version supported by pyvcloud.

        This case must deal with the possibility that the server API level is
        lower than the client in which case we'll get the highest level
        available on the server.
        """
        self._client = self._create_client_with_credentials(api_version=None)
        client_version = self._client.get_api_version()
        server_versions = self._client.get_supported_versions_list()
        self.assertTrue(
            client_version in server_versions,
            msg="Client version must be in server versions")

        if client.API_CURRENT_VERSIONS[-1] != self._client.get_api_version():
            # Server must be a lower version.
            self.assertEqual(client_version, server_versions[-1])

    def test_0020_change_api_version(self):
        """User can set API client to any supported server API version."""
        # First find the server versions.
        self._client = self._create_client_with_credentials(None)
        server_versions = self._client.get_supported_versions_list()
        self._client.logout()

        # Now prove we can login to any of them.
        for version in server_versions:
            self._logger.debug(
                "Login using server API version {0}".format(version))
            self._client = self._create_client_with_credentials(version)
            self._client.logout()

    def test_0030_server_highest_version(self):
        """User can set connection to highest supported server version."""
        self._client = client.Client(self._host, verify_ssl_certs=False)
        self._client.set_highest_supported_version()
        creds = client.BasicLoginCredentials(self._user, self._org, self._pass)
        self._client.set_credentials(creds)
        server_versions = self._client.get_supported_versions_list()

        self.assertEqual(
            self._client.get_api_version(),
            server_versions[-1],
            msg="Client version must be at highest server version level")

    def test_0040_flag_invalid_server_api(self):
        """Client returns an exception if user sets invalid server API."""
        try:
            self._client = self._create_client_with_credentials('99.99')
            self.fail("Login succeeded with bad API version")
        except VcdException:
            self._logger.debug("Received expected exception", exc_info=True)

    def test_0050_set_logging_parameters(self):
        """User can set logging parameters to force request logs.

        Resetting parameters does not change logging because there's only
        a single appender and it's already set by time this case runs. For
        now we just confirm that nothing breaks when these parameters are
        set.
        """
        self._client = client.Client(
            self._host,
            verify_ssl_certs=False,
            log_file='test_0050_set_logging_parameters.log',
            log_requests=True,
            log_headers=True,
            log_bodies=True)
        creds = client.BasicLoginCredentials(self._user, self._org, self._pass)
        self._client.set_credentials(creds)

    def test_0060_no_reuse_after_logout(self):
        """Client cannot be reused after logout."""
        self._client = self._create_client_with_credentials(None)
        self._logger.debug("Issuing org list request to prove liveness")
        self._client.get_org_list()
        self._client.logout()

        # Should not be possible to reuse after logout.
        unreachable_code = False
        try:
            self._client.get_org_list()
            # Can't use self.fail() as we have a general exception trap
            # around this block.
            unreachable_code = True
        except Exception:
            # We don't care about exception; reuse behavior is undefined.
            self._logger.debug(
                "Received exception after reusing logged out session",
                exc_info=True)

        if unreachable_code:
            self.fail("Org list succeeded after session logout!")

    def test_0070_flag_invalid_credentials(self):
        """Invalid credentials result in a VcdException."""
        self._logger.debug("TEST: test_0070_flag_invalid_credentials")
        self._client = client.Client(self._host, verify_ssl_certs=False)
        creds = client.BasicLoginCredentials(self._user, self._org, '!!!')
        try:
            self._client.set_credentials(creds)
            self.fail("Login succeeded with bad password")
        except VcdException:
            self._logger.debug("Received expected exception", exc_info=True)

    def test_0080_flag_invalid_host(self):
        """Invalid host results in an exception."""
        unreachable_code = False
        try:
            self._client = client.Client(
                "invalid.host.com",
                verify_ssl_certs=False)
            creds = client.BasicLoginCredentials(
                self._user,
                self._org,
                self._pass)
            self._client.set_credentials(creds)
        except Exception:
            # We don't care about the exact exception as request/urllib
            # handling is implementation-dependent and may change.
            self._logger.debug("Received expected exception", exc_info=True)

        if unreachable_code:
            raise Exception("Login succeeded with bad host")

    def _create_client_with_credentials(self, api_version):
        """Create client with[out] explicit API version and login."""
        new_client = client.Client(
            self._host,
            api_version=api_version,
            verify_ssl_certs=False)
        creds = client.BasicLoginCredentials(
            self._user, self._org, self._pass)
        new_client.set_credentials(creds)
        return new_client


if __name__ == '__main__':
    unittest.main()
