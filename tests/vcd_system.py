import unittest

from pyvcloud.vcd.system import System
from pyvcloud.vcd.test import TestCase


class TestSystem(TestCase):
    def test_create_org(self):
        sys_admin = self.client.get_admin()
        system = System(self.client, admin_resource=sys_admin)
        org = system.create_org(self.config['vcd']['org_name'],
                                self.config['vcd']['org_full_name'])
        assert org.get('name') == self.config['vcd']['org_name']

    def test_delete_org(self):
        system = System(self.client)
        system.delete_org(self.config['vcd']['org_name'], True, True)


if __name__ == '__main__':
    unittest.main()
