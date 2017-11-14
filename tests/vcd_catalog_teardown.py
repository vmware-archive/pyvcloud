import os
import unittest
import yaml
from pyvcloud.vcd.client import BasicLoginCredentials
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.test import TestCase

class TestCatalogTeardown(TestCase):

    def test_delete_catalog(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        catalog = org.delete_catalog(self.config['vcd']['catalog'])


if __name__ == '__main__':
    unittest.main()
