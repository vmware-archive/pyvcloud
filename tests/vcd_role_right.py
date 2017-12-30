# VMware vCloud Director Python SDK
# Copyright (c) 2017 VMware, Inc. All Rights Reserved.
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

import unittest

from pyvcloud.vcd.org import Org
from pyvcloud.vcd.role import Role
from pyvcloud.vcd.test import TestCase

class TestRole(TestCase):
    def test_01_list_role(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        roles = org.list_roles()
        assert len(roles) > 0

    def test_02_get_role(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        role = org.get_role(self.config['vcd']['role_name'])
        assert self.config['vcd']['role_name'] == role.get('name')

    def test_03_get_rights(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        role_name = self.config['vcd']['role_name']
        role_record = org.get_role(role_name)
        role = Role(self.client, href=role_record.get('href'))
        rights = role.list_rights()
        assert len(rights) > 0

    def test_04_create_role(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        role_name = self.config['vcd']['role_name']
        org.create_role(role_name, 'test description', ('Disk: View Properties',))
        role_record = org.get_role(role_name)
        assert self.config['vcd']['role_name'] == role_record.get('name')

    def test_05_list_rights_in_org(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        right_record_list = org.list_rights()
        assert len(right_record_list) > 0

    def test_06_delete_role_in_org(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        role_name = self.config['vcd']['role_name']
        org.delete_role(role_name)

if __name__ == '__main__':
    unittest.main()
