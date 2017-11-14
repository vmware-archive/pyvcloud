import os
import unittest
import yaml
from pyvcloud.vcd.client import BasicLoginCredentials
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.test import TestCase

class TestCatalogSetup(TestCase):

    def test_create_catalog(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        catalog = org.create_catalog(self.config['vcd']['catalog'], 'test catalog')
        assert self.config['vcd']['catalog'] == catalog.get('name')

    def test_upload_ova(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        template = org.upload_ovf(self.config['vcd']['catalog'],
                                  self.config['vcd']['local_template'])

    def test_validate_ova(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        template = org.get_catalog_item(self.config['vcd']['catalog'],
                                        self.config['vcd']['template'])
        assert self.config['vcd']['template'] == template.get('name')

if __name__ == '__main__':
    unittest.main()
