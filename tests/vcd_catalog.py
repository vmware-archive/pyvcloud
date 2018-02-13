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
from pyvcloud.vcd.test import TestCase


class TestCatalog(TestCase):
    def test_01_catalog_exists(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        catalog = org.get_catalog(self.config['vcd']['catalog'])
        assert self.config['vcd']['catalog'] == catalog.get('name')

    def test_02_change_catalog_owner(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        org.change_catalog_owner(self.config['vcd']['catalog'],
                                 self.config['vcd']['new_catalog_owner'])
        catalog_resource = org.get_catalog_resource(
            self.config['vcd']['catalog'], True)
        assert self.config['vcd']['new_catalog_owner'] \
               == catalog_resource.Owner.User.get('name')

    def test_03_remove_all_catalog_access(self):
        org_in_use = self.client.get_org_by_name(
            self.config['vcd']['org_in_use'])
        org = Org(self.client, resource=org_in_use)
        control_access = org.remove_catalog_access_settings(
            self.config['vcd']['catalog'], remove_all=True)
        self.assertFalse(hasattr(control_access, 'AccessSettings'))

    def test_04_add_catalog_access(self):
        org_in_use = self.client.get_org_by_name(
            self.config['vcd']['org_in_use'])
        org = Org(self.client, resource=org_in_use)
        control_access = org.add_catalog_access_settings(
            self.config['vcd']['catalog'],
            access_settings_list=[
                {'name': self.config['vcd']['access_user1'], 'type': 'user',
                 'access_level': 'ReadOnly'},
                {'name': self.config['vcd']['access_user'], 'type': 'user',
                 'access_level':'Change'},
                {'name': self.config['vcd']['access_org'], 'type': 'org',
                 'access_level': 'ReadOnly'}

            ])
        assert len(control_access.AccessSettings.AccessSetting) == 3

    def test_05_catalog_control_access_retrieval(self):
        org_in_use = self.client.get_org_by_name(
            self.config['vcd']['org_in_use'])
        org = Org(self.client, resource=org_in_use)
        catalog = org.get_catalog(self.config['vcd']['catalog'])
        assert self.config['vcd']['catalog'] == catalog.get('name')
        control_access = org.get_catalog_access_settings(catalog.get('name'))
        assert len(control_access.AccessSettings.AccessSetting) == 3

    def test_06_remove_catalog_access(self):
        org_in_use = self.client.get_org_by_name(
            self.config['vcd']['org_in_use'])
        org = Org(self.client, resource=org_in_use)
        control_access = org.remove_catalog_access_settings(
            self.config['vcd']['catalog'],
            access_settings_list=[
                {'name': self.config['vcd']['access_user'], 'type': 'user'},
                {'name': self.config['vcd']['access_org'], 'type': 'org'}

            ])
        assert len(control_access.AccessSettings.AccessSetting) == 1

    def test_07_remove_non_existing_catalog_access(self):
        org_in_use = self.client.get_org_by_name(
            self.config['vcd']['org_in_use'])
        org = Org(self.client, resource=org_in_use)
        try:
            org.remove_catalog_access_settings(
                self.config['vcd']['catalog'],
                access_settings_list=[
                    {'name': self.config['vcd']['access_org'], 'type': 'user'}
                ])
            self.fail("Removing non existing acl should fail")
        except Exception:
            pass

    def test_08_catalog_share_access(self):
        org_in_use = self.client.get_org_by_name(
            self.config['vcd']['org_in_use'])
        org = Org(self.client, resource=org_in_use)
        control_access = org.share_catalog_with_org_members(
            self.config['vcd']['catalog'],
            everyone_access_level='ReadOnly')
        assert control_access.IsSharedToEveryone.text == 'true'
        assert control_access.EveryoneAccessLevel.text == 'ReadOnly'

    def test_09_catalog_unshare_access(self):
        org_in_use = self.client.get_org_by_name(
            self.config['vcd']['org_in_use'])
        org = Org(self.client, resource=org_in_use)
        control_access = org.unshare_catalog_with_org_members(
            self.config['vcd']['catalog'])
        assert control_access.IsSharedToEveryone.text == 'false'

    def test_10_remove_last_catalog_access(self):
        org_in_use = self.client.get_org_by_name(
            self.config['vcd']['org_in_use'])
        org = Org(self.client, resource=org_in_use)
        control_access = org.remove_catalog_access_settings(
            self.config['vcd']['catalog'],
            access_settings_list=[
                {'name': self.config['vcd']['access_user1'], 'type': 'user'}
            ])
        self.assertFalse(hasattr(control_access, 'AccessSettings'))


if __name__ == '__main__':
    unittest.main()
