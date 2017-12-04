import unittest

from pyvcloud.vcd.org import Org
from pyvcloud.vcd.system import System
from pyvcloud.vcd.test import TestCase


class TestOrg(TestCase):
    def test_01_create_org(self):
        sys_admin = self.client.get_admin()
        system = System(self.client, admin_resource=sys_admin)
        org = system.create_org(self.config['vcd']['org_name'],
                                self.config['vcd']['org_full_name'])
        assert org.get('name') == self.config['vcd']['org_name']

    def test_02_update_enable_org(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        updated_org = org.update_org(self.config['vcd']['org_name'], True)
        self.assertTrue(updated_org['IsEnabled'])

    def test_03_update_disable_org(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        updated_org = org.update_org(self.config['vcd']['org_name'], False)
        self.assertFalse(updated_org['IsEnabled'])

    def test_04_delete_org(self):
        system = System(self.client)
        system.delete_org(self.config['vcd']['org_name'], True, True)


if __name__ == '__main__':
    unittest.main()
