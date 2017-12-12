import unittest

from pyvcloud.vcd.org import Org
from pyvcloud.vcd.test import TestCase
from pyvcloud.vcd.vdc import VDC


class TestVDC(TestCase):

    def test_list_vdc(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdcs = org.list_vdcs()
        assert len(vdcs) > 0

    def test_get_vdc(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')

    def test_vdc_control_access_retrieval(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=vdc_resource)
        access_control = vdc.get_access_control_settings()
        assert len(access_control) > 0


if __name__ == '__main__':
    unittest.main()
