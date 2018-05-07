import os

import unittest
import yaml

from pyvcloud.system_test_framework.environment import Environment


class BaseTestCase(unittest.TestCase):
    _config_file = 'base_config.yaml'
    _config_yaml = None

    @classmethod
    def setUpClass(cls):
        if 'VCD_TEST_BASE_CONFIG_FILE' in os.environ:
            cls._config_file = os.environ['VCD_TEST_BASE_CONFIG_FILE']
        with open(cls._config_file, 'r') as f:
            cls._config_yaml = yaml.load(f)

        Environment.init(cls._config_yaml)
        Environment.attach_vc()
        Environment.create_pvdc()
        Environment.create_org()
        Environment.create_users()
        Environment.create_ovdc()
        Environment.create_ovdc_network()
        Environment.create_catalog()
        Environment.share_catalog()
        Environment.upload_template()
        Environment.instantiate_vapp()

    @classmethod
    def tearDownClass(cls):
        Environment.cleanup()
