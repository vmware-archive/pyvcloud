import os
import unittest
import yaml
from pyvcloud.vcd.client import BasicLoginCredentials
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.test import TestCase

class TestCatalog(TestCase):

    def test_catalog_exists(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        catalog = org.get_catalog(self.config['vcd']['catalog'])
        assert self.config['vcd']['catalog'] == catalog.get('name')

    def test_catalog_control_access_retrieval(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        catalog = org.get_catalog(self.config['vcd']['catalog'])
        assert self.config['vcd']['catalog'] == catalog.get('name')
        control_access = org.get_catalog_access_control_settings(catalog.get('name'))
        assert control_access is not None

if __name__ == '__main__':
    unittest.main()
