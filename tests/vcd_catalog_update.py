import os
import unittest
import yaml
from pyvcloud.vcd.client import BasicLoginCredentials
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.test import TestCase

class UpdateCatalog(TestCase):

    def test_create_catalog(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        catalog = org.create_catalog(self.config['vcd']['catalog'], 'test catalog')
        assert self.config['vcd']['catalog'] == catalog.get('name')

    def test_update_catalog(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        catalog = org.update_catalog(self.config['vcd']['catalog'],
           self.config['vcd']['new_name'], self.config['vcd']['new_desc'])
        assert self.config['vcd']['new_name'] == catalog.get('name')
        assert self.config['vcd']['new_desc'] == catalog['Description']

if __name__ == '__main__':
    unittest.main()
