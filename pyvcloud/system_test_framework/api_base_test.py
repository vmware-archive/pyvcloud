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

import os
import unittest

from pyvcloud.system_test_framework.environment import Environment
from pyvcloud.vcd.vcd_client import VcdClient
from pyvcloud.vcd.client import BasicLoginCredentials
import yaml


class ApiBaseTestCase(unittest.TestCase):
    _config_file = 'base_config.yaml'
    _config_yaml = None

    @classmethod
    def setUpClass(cls):
        if 'VCD_TEST_BASE_CONFIG_FILE' in os.environ:
            cls._config_file = os.environ['VCD_TEST_BASE_CONFIG_FILE']
        with open(cls._config_file, 'r') as f:
            cls._config_yaml = yaml.safe_load(f)

        Environment.init(cls._config_yaml)
        cls._logger = Environment.get_default_logger()
        cls._client = cls._create_client_with_credentials()
        if not cls._client:
            raise Exception("Failed to create VCD session")

    @classmethod
    def tearDownClass(cls):
        Environment.cleanup()
        if cls._client is not None:
            try:
                cls._logger.info("Logging out client automatically")
                cls._client.logout()
            except Exception:
                cls._logger.warning("Client logout failed",
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
