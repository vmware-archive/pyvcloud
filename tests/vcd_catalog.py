import os
import unittest
import yaml
from pyvcloud.vcd.client import BasicLoginCredentials
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.org import Org

class TestLogin(unittest.TestCase):

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
        result = cls.client.set_credentials(BasicLoginCredentials(
            cls.config['vcd']['user'],
            cls.config['vcd']['org'],
            cls.config['vcd']['password']))

    @classmethod
    def tearDownClass(cls):
        result = cls.client.logout()

    def test_catalog(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, org_resource=logged_in_org)
        catalog = org.get_catalog(self.config['vcd']['catalog'])
        assert self.config['vcd']['catalog'] == catalog.get('name')


if __name__ == '__main__':
    unittest.main()
