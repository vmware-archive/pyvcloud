import unittest

from pyvcloud.vcd.org import Org
from pyvcloud.vcd.test import TestCase
from pyvcloud.vcd.vdc import VDC


class TestEdgeGateway(TestCase):

    def test_001_list_edge_gateways(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=v)
        edge_gateways = vdc.list_edge_gateways()
        assert len(edge_gateways) > 0
