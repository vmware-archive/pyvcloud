import unittest

from pyvcloud.vcd.org import Org
from pyvcloud.vcd.role import Role
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

    def test_get_rights(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        role_name = self.config['vcd']['role_name']
        role_record = org.get_role(role_name)
        role = Role(self.client, href=role_record.get('href'))
        rights = role.list_rights()
        assert len(rights) > 0

if __name__ == '__main__':
    unittest.main()
