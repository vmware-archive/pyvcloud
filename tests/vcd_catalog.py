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


if __name__ == '__main__':
    unittest.main()
