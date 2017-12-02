# VMware vCloud Director Python SDK
# Copyright (c) 2017 VMware, Inc. All Rights Reserved.
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
from pyvcloud.vcd.client import BasicLoginCredentials
from pyvcloud.vcd.client import Client
import unittest
import yaml


class TestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config_file = 'config.yml'
        if 'VCD_TEST_CONFIG_FILE' in os.environ:
            config_file = os.environ['VCD_TEST_CONFIG_FILE']
        with open(config_file, 'r') as f:
            cls.config = yaml.load(f)
        cls.client = Client(cls.config['vcd']['host'],
                            api_version=cls.config['vcd']['api_version'],
                            verify_ssl_certs=cls.config['vcd']['verify'],
                            log_file='pyvcloud.log',
                            log_requests=True,
                            log_headers=True,
                            log_bodies=True
                            )
        cls.client.set_credentials(BasicLoginCredentials(
            cls.config['vcd']['user'],
            cls.config['vcd']['org'],
            cls.config['vcd']['password']))

    @classmethod
    def tearDownClass(cls):
        cls.client.logout()
