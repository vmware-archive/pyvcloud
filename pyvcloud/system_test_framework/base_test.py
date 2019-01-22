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
import yaml


class BaseTestCase(unittest.TestCase):
    _config_file = 'base_config.yaml'
    _config_yaml = None

    @classmethod
    def setUpClass(cls):
        if 'VCD_TEST_BASE_CONFIG_FILE' in os.environ:
            cls._config_file = os.environ['VCD_TEST_BASE_CONFIG_FILE']
        with open(cls._config_file, 'r') as f:
            cls._config_yaml = yaml.safe_load(f)

        Environment.init(cls._config_yaml)
        Environment.attach_vc()
        Environment.create_pvdc()
        Environment.create_external_network()
        Environment.create_org()
        Environment.create_users()
        Environment.create_ovdc()
        Environment.create_direct_ovdc_network()
        Environment.create_advanced_gateway()
        Environment.create_ovdc_network()
        Environment.create_routed_ovdc_network()
        Environment.create_catalog()
        Environment.share_catalog()
        Environment.upload_template()

    @classmethod
    def tearDownClass(cls):
        Environment.cleanup()
