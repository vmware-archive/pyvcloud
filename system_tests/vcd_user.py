# VMware vCloud Director Python SDK
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
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
from uuid import uuid1

from pyvcloud.system_test_framework.base_test import BaseTestCase
from pyvcloud.system_test_framework.environment import developerModeAware
from pyvcloud.system_test_framework.environment import Environment

from pyvcloud.vcd.client import TaskStatus
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.system import System


class TestUser(BaseTestCase):
    """Test Org User functionality implemented in pyvcloud."""

    # All tests in this module should run as System Administrator.
    _client = None

    _new_org_name = 'test_org_' + str(uuid1())
    _new_org_full_name = 'Test Org'
    _new_org_enabled = True
    _new_org_admin_href = None
    _org = None

    _org_user = 'test_org_user'
    _vapp_author_role = 'vApp Author'
    _vapp_user_role = 'vApp User'

    def test_0000_setup(self):
        """Setup a Org required for other tests in this module.

        Create an Org as per the configuration stated above. Tests
        System.create_org() method.

        This test passes if org href is not None.
        """
        TestUser._client = Environment.get_sys_admin_client()
        sys_admin_resource = TestUser._client.get_admin()
        system = System(TestUser._client, admin_resource=sys_admin_resource)
        result = system.create_org(TestUser._new_org_name,
                                   TestUser._new_org_full_name,
                                   TestUser._new_org_enabled)
        TestUser._new_org_admin_href = result.get('href')

        TestUser._org = Org(TestUser._client,
                            href=TestUser._new_org_admin_href)

        self.assertIsNotNone(TestUser._new_org_admin_href)

    def test_0010_create_user(self):
        """Test the method Client.create_user().

        Test passes if the created user_name in the organization matches the
        retrieved user_name from the organization.
        """
        logger = Environment.get_default_logger()
        role = TestUser._org.get_role_record(TestUser._vapp_user_role)
        role_href = role.get('href')

        logger.debug('Creating user with vApp User role')
        created_user = TestUser._org.create_user(TestUser._org_user,
                                                 "password",
                                                 role_href,
                                                 "Full Name",
                                                 "Description",
                                                 "xyz@mail.com",
                                                 "408-487-9087",
                                                 "test_user_im",
                                                 "xyz@mail.com",
                                                 "Alert Vcd:",
                                                 is_enabled=False)

        self.assertEqual(created_user.get('name'), TestUser._org_user)

    def test_0020_get_user(self):
        """Test the  method Client.get_user().

        This test passes if the organization user name detail retrieved by the
        method is not None, and created user name matches retrieved user name.
        """
        org_user = TestUser._org.get_user(TestUser._org_user)
        self.assertIsNotNone(org_user)
        registered_org_user = org_user.get('name')

        self.assertEqual(registered_org_user, TestUser._org_user)

    def test_0030_enable_user(self):
        """Test the method Client.update_user().

        This test passes if the method is can successfully enable created
        user.
        """
        updated_user = TestUser._org.update_user(TestUser._org_user,
                                                 is_enabled=True)

        self.assertTrue(updated_user['IsEnabled'])

    def test_0040_update_user_role(self):
        """Test the method Client.update_user().

        This test passes if the method is able to update an existing user role
        with a supplied user role.
        """
        logger = Environment.get_default_logger()
        logger.debug('Update org_user role from vApp User tp vApp Author')
        updated_user = TestUser._org.update_user(
            TestUser._org_user, role_name=TestUser._vapp_author_role)
        updated_user_role = updated_user['Role'].get('name')

        self.assertEqual(updated_user_role, TestUser._vapp_author_role)

    def test_0050_delete_user(self):
        """Test the method Client.delete_user().

        This test passes if no errors are generated while deleting org user.
        """
        TestUser._org.delete_user(user_name=TestUser._org_user)

    @developerModeAware
    def test_9998_teardown(self):
        """Test the method System.delete_org() with force = recursive = True.

        Invoke the method for the organization created by setup.

        This test passes if no errors are generated while deleting the org.
        """
        sys_admin_resource = TestUser._client.get_admin()
        system = System(TestUser._client, admin_resource=sys_admin_resource)
        task = system.delete_org(org_name=TestUser._new_org_name,
                                 force=True,
                                 recursive=True)
        result = TestUser._client.get_task_monitor().\
            wait_for_success(task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_9999_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestUser._client.logout()


if __name__ == '__main__':
    unittest.main()
