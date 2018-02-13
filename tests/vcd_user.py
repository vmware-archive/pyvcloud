# VMware vCloud Director Python SDK
# Copyright (c) 2017-2018 VMware, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import random
import string
import unittest

from pyvcloud.vcd.org import Org
from pyvcloud.vcd.test import TestCase


class TestUser(TestCase):
    def create_user(self, user_name, enabled=False):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        role = org.get_role_record(self.config['vcd']['role_name'])
        role_href = role.get('href')
        return org.create_user(user_name, "password", role_href, "Full Name",
                               "Description", "xyz@mail.com", "408-487-9087",
                               "test_user_im", "xyz@mail.com", "Alert Vcd:",
                               is_enabled=enabled)

    def delete_user(self, user_name):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        org.delete_user(user_name)

    def update_user(self, user_name, is_enabled):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        return org.update_user(user_name, is_enabled)

    def test_00_list_users(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        users = org.list_users()
        assert len(users) > 0

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
