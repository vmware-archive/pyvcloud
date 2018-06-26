# VMware vCloud Director Python SDK
# Copyright (c) 2018 VMware, Inc. All Rights Reserved.
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
from pyvcloud.vcd.exceptions import EntityNotFoundException
from pyvcloud.vcd.exceptions import VcdTaskException
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.system import System


class TestOrg(BaseTestCase):
    """Test Org functionalities implemented in pyvcloud."""

    # All tests in this module should be run as System Administrator
    _client = None

    _new_org_name = 'test_org_' + str(uuid1())
    _new_org_full_name = 'Test Org'
    _new_org_enabled = True
    _new_org_admin_href = None

    _non_existent_org_name = '_non_existent_org_' + str(uuid1())

    def test_0000_setup(self):
        """Setup a Org required for other tests in this module.

        Create an Org as per the configuration stated above. Tests
        System.create_org() method.

        This test passes if org href is not None.
        """
        TestOrg._client = Environment.get_sys_admin_client()
        sys_admin_resource = TestOrg._client.get_admin()
        system = System(TestOrg._client, admin_resource=sys_admin_resource)
        result = system.create_org(TestOrg._new_org_name,
                                   TestOrg._new_org_full_name,
                                   TestOrg._new_org_enabled)
        TestOrg._new_org_admin_href = result.get('href')

        self.assertIsNotNone(TestOrg._new_org_admin_href)

    def test_0010_list_orgs(self):
        """Test the  method Client.get_org_list().

        This test passes if the expected organization name is in the list of
        organizations returned by the method.
        """
        orgs = TestOrg._client.get_org_list()
        org_names = []
        for org_resource in orgs:
            org_names.append(org_resource.get('name'))

        self.assertIn(TestOrg._new_org_name, org_names)

    def test_0020_get_org(self):
        """Test the  method Client.get_org_by_name().

        Invoke the method with the name of the organization created in setup.

        This test passes if the organization detail retrieved by the method is
        not None, and the details e.g. name of the organization, are correct.
        """
        org_resource = TestOrg._client.get_org_by_name(TestOrg._new_org_name)
        self.assertIsNotNone(org_resource)
        org = Org(TestOrg._client, resource=org_resource)
        self.assertEqual(TestOrg._new_org_name, org.get_name())

    def test_0030_get_non_existent_org(self):
        """Test the  method Client.get_org_by_name().

        Invoke the method with the name of a bogus organization.

        This test passes if the operation fails with an
        EntityNotFoundException.
        """
        try:
            TestOrg._client.get_org_by_name(TestOrg._non_existent_org_name)
            self.fail('Should not be able to fetch organization ' +
                      TestOrg._non_existent_org_name)
        except EntityNotFoundException as e:
            return

    def test_0040_enable_disable_org(self):
        """Test the  method Org.update_org().

        First disable the organization then re-enable it.

        This test passes if the state of organization matches our expectation
        after each operation.
        """
        logger = Environment.get_default_logger()
        org = Org(TestOrg._client, href=TestOrg._new_org_admin_href)
        logger.debug('Disabling org: ' + TestOrg._new_org_name)
        updated_org = org.update_org(is_enabled=False)
        self.assertFalse(updated_org['IsEnabled'])

        logger.debug('Re-enabling org: ' + TestOrg._new_org_name)
        updated_org = org.update_org(is_enabled=True)
        self.assertTrue(updated_org['IsEnabled'])

    def test_0050_delete_no_force_enabled_org(self):
        """Test the method System.delete_org() with force = recursive = False.

        Invoke delete operation on an enabled organization with 'force' and
        'recursive' flag set to False. An enabled organization can't be deleted
        unless 'force' flag is set to True.

        This test passes if the operation fails with a VcdTaskException.
        """
        try:
            sys_admin_resource = TestOrg._client.get_admin()
            system = System(TestOrg._client, admin_resource=sys_admin_resource)
            task = system.delete_org(org_name=TestOrg._new_org_name,
                                     force=False,
                                     recursive=False)
            TestOrg._client.get_task_monitor().wait_for_success(task=task)
            self.fail('Deletion of org ' + TestOrg._new_org_name + 'shouldn\'t'
                      'succeeded.')
        except VcdTaskException as e:
            return

    @developerModeAware
    def test_9998_teardown(self):
        """Test the method System.delete_org() with force = recursive = True.

        Invoke the method for the organization created by setup.

        This test passes if no errors are generated while deleting the org.
        """
        sys_admin_resource = TestOrg._client.get_admin()
        system = System(TestOrg._client, admin_resource=sys_admin_resource)
        task = system.delete_org(org_name=TestOrg._new_org_name,
                                 force=True,
                                 recursive=True)
        result = TestOrg._client.get_task_monitor().wait_for_success(task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_9999_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestOrg._client.logout()


if __name__ == '__main__':
    unittest.main()
