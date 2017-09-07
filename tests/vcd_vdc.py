import os
import unittest
import yaml
from pyvcloud.vcd.client import BasicLoginCredentials
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.test import TestCase
from pyvcloud.vcd.vdc import VDC

class TestVDC(TestCase):

    def test_list_vdc(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, org_resource=logged_in_org)
        vdcs = org.list_vdcs()
        assert len(vdcs) > 0

    def test_get_vdc(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, org_resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, vdc_href=v.get('href'))
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')

if __name__ == '__main__':
    unittest.main()
