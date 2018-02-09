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
        role = org.get_role_record(self.config['vcd']['role_name'])
        assert self.config['vcd']['role_name'] == role.get('name')

    def test_03_get_rights(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        role_name = self.config['vcd']['role_name']
        role_record = org.get_role_record(role_name)
        role = Role(self.client, href=role_record.get('href'))
        rights = role.list_rights()
        assert len(rights) > 0

    def test_04_create_role(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        role_name = self.config['vcd']['role_name']
        org.create_role(role_name, 'test description', ('Disk: View Properties',))
        role_record = org.get_role_record(role_name)
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

    def test_07_link_role_to_template(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        role_name = self.config['vcd']['role_name']
        role_record = org.get_role_record(role_name)
        role = Role(self.client, href=role_record.get('href'))
        role.link()

    def test_08_unlink_role_from_template(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        role_name = self.config['vcd']['role_name']
        role_record = org.get_role_record(role_name)
        role = Role(self.client, href=role_record.get('href'))
        role.unlink()

    def test_09_add_rights_to_Role(self):
        org_in_use = self.config['vcd']['org_in_use']
        org = Org(self.client, href=self.client.get_org_by_name(org_in_use).get('href'))
        role_name = self.config['vcd']['role_name']
        right_name = self.config['vcd']['right_name']

        role_record = org.get_role_record(role_name)
        role = Role(self.client, href=role_record.get('href'))

        updated_role_resource = role.add_rights([right_name], org)
        success = False
        if hasattr(updated_role_resource, 'RightReferences') and \
                hasattr(updated_role_resource.RightReferences, 'RightReference'):
            for right in updated_role_resource.RightReferences.RightReference:
                if right.get('name') == right_name:
                    success = True
                    break
        assert success

    def test_10_remove_rights_from_role(self):
        org_in_use = self.config['vcd']['org_in_use']
        org = Org(self.client, href = self.client.get_org_by_name(org_in_use).get('href'))
        role_name = self.config['vcd']['role_name']
        right_name = self.config['vcd']['right_name']

        role_record = org.get_role_record(role_name)
        role = Role(self.client, href=role_record.get('href'))

        updated_role_resource = role.remove_rights([right_name])
        success = True
        if hasattr(updated_role_resource, 'RightReferences') and \
                hasattr(updated_role_resource.RightReferences, 'RightReference'):
            for right in updated_role_resource.RightReferences.RightReference:
                if right.get('name') == right_name:
                    success = False
                    break
        assert success

    def test_11_add_rights_to_org(self):
        org_in_use = self.config['vcd']['org_in_use']
        org = Org(self.client, href=self.client.get_org_by_name(org_in_use).get('href'))
        role_name = self.config['vcd']['role_name']
        right_name = self.config['vcd']['right_name']
        right_record_list = org.list_rights_of_org()
        no_of_rights_before = len(right_record_list)
        org.add_rights([right_name])
        org.reload()
        right_record_list = org.list_rights_of_org()
        no_of_rights_after = len(right_record_list)
        assert no_of_rights_before < no_of_rights_after

    def test_12_remove_rights_from_org(self):
        org_in_use = self.config['vcd']['org_in_use']
        org = Org(self.client, href=self.client.get_org_by_name(org_in_use).get('href'))
        right_name = self.config['vcd']['right_name']
        right_record_list = org.list_rights_of_org()
        no_of_rights_before = len(right_record_list)
        org.remove_rights([right_name])
        org.reload()
        right_record_list = org.list_rights_of_org()
        no_of_rights_after = len(right_record_list)
        assert no_of_rights_before > no_of_rights_after

if __name__ == '__main__':
    unittest.main()
