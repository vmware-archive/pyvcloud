import unittest
import string
import random

from pyvcloud.vcd.org import Org
from pyvcloud.vcd.test import TestCase


class TestUser(TestCase):
    @classmethod
    def get_org(cls):
        logged_in_org = cls.client.get_org()
        org = Org(cls.client, resource=logged_in_org,
                  is_admin=cls.is_sys_admin(logged_in_org))
        return org

    @staticmethod
    def is_sys_admin(logged_in_org):
        return logged_in_org.get('name') == 'System'

    def create_user(self, user_name, enabled=False):
        org = self.get_org()
        role = org.get_role(self.config['vcd']['role_name'])
        role_href = role.get('href')
        return org.create_user(user_name, "password", role_href, "Full Name",
                               "Description", "xyz@mail.com", "408-487-9087",
                               "test_user_im", "xyz@mail.com", "Alert Vcd:",
                               is_enabled=enabled)

    def delete_user(self, user_name):
        org = self.get_org()
        result = org.delete_user(user_name)
        print(result)

    def update_user(self, user_name, is_enabled):
        org = self.get_org()
        return org.update_user(user_name, is_enabled)

    def test_01_create_and_delete_user(self):
        user_name = self.config['vcd']['user_name'].join(
            random.sample(string.ascii_lowercase, 8))
        user = self.create_user(user_name)
        assert user_name == user.get('name')
        self.delete_user(user_name)

    def test_02_create_enable_delete_user(self):
        user_name = self.config['vcd']['user_name'].join(
            random.sample(string.ascii_lowercase, 8))
        self.create_user(user_name, False)
        updated_user = self.update_user(user_name, True)
        self.assertTrue(updated_user['IsEnabled'])
        self.delete_user(user_name)

    def test_03_create_disable_delete_user(self):
        user_name = self.config['vcd']['user_name'].join(
            random.sample(string.ascii_lowercase, 8))
        self.create_user(user_name, True)
        updated_user = self.update_user(user_name, False)
        self.assertFalse(updated_user['IsEnabled'])
        self.delete_user(user_name)


if __name__ == '__main__':
    unittest.main()
