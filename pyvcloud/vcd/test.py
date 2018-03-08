# VMware vCloud Director Python SDK
# Copyright (c) 2017-2018 VMware, Inc. All Rights Reserved.
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

import logging
import os
import unittest
import warnings

import requests
import yaml

from pyvcloud.vcd.client import BasicLoginCredentials
from pyvcloud.vcd.client import Client


class TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config_file = 'config.yml'
        if 'VCD_TEST_CONFIG_FILE' in os.environ:
            config_file = os.environ['VCD_TEST_CONFIG_FILE']
        with open(config_file, 'r') as f:
            cls.config = yaml.load(f)
        if not cls.config['vcd']['verify'] and \
                cls.config['vcd']['disable_ssl_warnings']:
            requests.packages.urllib3.disable_warnings()
        cls.client = Client(
            cls.config['vcd']['host'],
            api_version=cls.config['vcd']['api_version'],
            verify_ssl_certs=cls.config['vcd']['verify'],
            log_file='pyvcloud.log',
            log_requests=True,
            log_headers=True,
            log_bodies=True)
        cls.client.set_credentials(
            BasicLoginCredentials(cls.config['vcd']['user'],
                                  cls.config['vcd']['org'],
                                  cls.config['vcd']['password']))
        logging.basicConfig(
            filename='tests.log',
            level=logging.DEBUG,
            format='%(asctime)s %(name)-12s %(lineno)s '
            '%(levelname)-8s %(message)s',
            datefmt='%m-%d %H:%M:%S')
        cls.logger = logging.getLogger(__name__)

    @classmethod
    def tearDownClass(cls):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ResourceWarning) # NOQA
            cls.client.logout()
