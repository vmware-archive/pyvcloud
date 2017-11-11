import unittest

from pyvcloud.vcd.org import Org
from pyvcloud.vcd.test import TestCase


class TestRole(TestCase):
    def test_list_role(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org, is_admin=True)
        roles = org.list_roles()
        assert len(roles) > 0

    def test_get_role(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org, is_admin=True)
        role = org.get_role(self.config['vcd']['role_name'])
        assert self.config['vcd']['role_name'] == role.get('name')


if __name__ == '__main__':
    unittest.main()
