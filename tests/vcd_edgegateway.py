import unittest

from pyvcloud.vcd.org import Org
from pyvcloud.vcd.test import TestCase
from pyvcloud.vcd.vdc import VDC


class TestEdgeGateway(TestCase):

    def test_001_list_edgegateways(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))
        edgeGateways = vdc.list_edgegateways()
        assert len(edgeGateways) > 0
