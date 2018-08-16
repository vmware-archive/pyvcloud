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

from uuid import uuid1

from pyvcloud.system_test_framework.base_test import BaseTestCase
from pyvcloud.system_test_framework.environment import CommonRoles
from pyvcloud.system_test_framework.environment import developerModeAware
from pyvcloud.system_test_framework.environment import Environment

from pyvcloud.vcd.exceptions import EntityNotFoundException
from pyvcloud.vcd.exceptions import OperationNotSupportedException
from pyvcloud.vcd.vdc import VDC


class TestOrgVDC(BaseTestCase):
    """Test OrgVDC functionalities implemented in pyvcloud."""

    # All tests in this module should run as System Administrator.
    _client = None

    _new_vdc_name = 'org_vdc_' + str(uuid1())
    _new_vdc_href = None
    _non_existent_vdc_name = 'non_existent_org_vdc_' + str(uuid1())

    def test_0000_setup(self):
        """Setup the org vdc required for the other tests in this module.

        Create one org vdc as per the configuration stated above. Test the
        method Org.create_org_vdc().

        This test passes if the vdc href is not None.
        """
        logger = Environment.get_default_logger()
        TestOrgVDC._client = Environment.get_sys_admin_client()
        org = Environment.get_test_org(TestOrgVDC._client)

        vdc_name = TestOrgVDC._new_vdc_name
        pvdc_name = Environment.get_test_pvdc_name()
        storage_profiles = [{
            'name': '*',
            'enabled': True,
            'units': 'MB',
            'limit': 0,
            'default': True
        }]

        vdc_resource = org.create_org_vdc(
            vdc_name,
            pvdc_name,
            storage_profiles=storage_profiles,
            uses_fast_provisioning=True,
            is_thin_provision=True)
        TestOrgVDC._client.get_task_monitor().wait_for_success(
            task=vdc_resource.Tasks.Task[0])

        logger.debug('Created ovdc ' + vdc_name + '.')

        # The following contraption is required to get the non admin href of
        # the ovdc. vdc_resource contains the admin version of the href since
        # we created the ovdc as a sys admin.
        org.reload()
        for vdc in org.list_vdcs():
            if vdc.get('name').lower() == vdc_name.lower():
                TestOrgVDC._new_vdc_href = vdc.get('href')

        self.assertIsNotNone(TestOrgVDC._new_vdc_href)

    def test_0010_list_vdc(self):
        """Test the method VDC.list_vdcs().

        This test passes if the vdc created during setup can be found in the
        list of vdcs retrieved.
        """
        org = Environment.get_test_org(TestOrgVDC._client)
        vdc_list = org.list_vdcs()

        retrieved_vdc_names = []
        retrieved_vdc_hrefs = []
        for vdc in vdc_list:
            retrieved_vdc_names.append(vdc['name'])
            retrieved_vdc_hrefs.append(vdc['href'])

        self.assertIn(TestOrgVDC._new_vdc_name, retrieved_vdc_names)
        self.assertIn(TestOrgVDC._new_vdc_href, retrieved_vdc_hrefs)

    def test_0020_get_vdc(self):
        """Test the method VDC.get_vdc().

        This test passes if the expected vdc can be successfully retrieved by
        name.
        """
        org = Environment.get_test_org(TestOrgVDC._client)
        vdc = org.get_vdc(TestOrgVDC._new_vdc_name)

        self.assertEqual(TestOrgVDC._new_vdc_name, vdc.get('name'))
        self.assertEqual(TestOrgVDC._new_vdc_href, vdc.get('href'))

    def test_0030_get_non_existent_vdc(self):
        """Test the method VDC.get_vdc().

        This test passes if the non-existent vdc can't be successfully
        retrieved by name.
        """
        org = Environment.get_test_org(TestOrgVDC._client)
        try:
            org.get_vdc(TestOrgVDC._non_existent_vdc_name)
            self.fail('Should not be able to fetch vdc ' +
                      TestOrgVDC._non_existent_vdc_name)
        except EntityNotFoundException as e:
            pass

    def test_0040_enable_disable_vdc(self):
        """Test the method VDC.enable_vdc().

        First disable the vdc, try to re-disable it (which should fail). Next,
        enable the vdc back, and then try to re-enable the vdc (which should
        fail).

        This test passes if the state of vdc matches our expectation after each
        operation.
        """
        logger = Environment.get_default_logger()
        vdc = VDC(TestOrgVDC._client, href=TestOrgVDC._new_vdc_href)
        # vdc should be in enabled state after the previous tests.

        vdc.enable_vdc(enable=False)
        logger.debug('Disabled vdc ' + TestOrgVDC._new_vdc_name + '.')
        try:
            logger.debug('Trying to again disable vdc ' +
                         TestOrgVDC._new_vdc_name + '.')
            vdc.enable_vdc(enable=False)
            self.fail('Should not be able to disable vdc ' +
                      TestOrgVDC._new_vdc_href)
        except OperationNotSupportedException as e:
            pass

        vdc.enable_vdc(enable=True)
        logger.debug('Enabled vdc ' + TestOrgVDC._new_vdc_name + '.')
        try:
            logger.debug('Trying to again enable vdc ' +
                         TestOrgVDC._new_vdc_name + '.')
            vdc.enable_vdc(enable=True)
            self.fail('Should not be able to enable vdc ' +
                      TestOrgVDC._new_vdc_href)
        except OperationNotSupportedException as e:
            pass

    def test_0050_vdc_acl(self):
        """Test the methods related to access control list in vdc.py.

        This test passes if all the acl operations are successful.
        """
        logger = Environment.get_default_logger()
        vdc = VDC(TestOrgVDC._client, href=TestOrgVDC._new_vdc_href)
        vdc_name = TestOrgVDC._new_vdc_name

        vapp_user_name = Environment.get_username_for_role_in_test_org(
            CommonRoles.VAPP_USER)
        console_user_name = Environment.get_username_for_role_in_test_org(
            CommonRoles.CONSOLE_ACCESS_ONLY)

        # remove all
        logger.debug('Removing all access control from vdc ' + vdc_name)
        control_access = vdc.remove_access_settings(remove_all=True)
        self.assertFalse(hasattr(control_access, 'AccessSettings'))

        # add
        logger.debug('Adding 2 access control rule to vdc ' + vdc_name)
        vdc.reload()
        control_access = vdc.add_access_settings(
            access_settings_list=[{
                'name': vapp_user_name,
                'type': 'user'
            }, {
                'name': console_user_name,
                'type': 'user',
                'access_level': 'ReadOnly'
            }])
        self.assertEqual(len(control_access.AccessSettings.AccessSetting), 2)

        # get
        logger.debug('Fetching access control rules for vdc ' + vdc_name)
        vdc.reload()
        control_access = vdc.get_access_settings()
        self.assertEqual(len(control_access.AccessSettings.AccessSetting), 2)

        # remove
        logger.debug('Removing 1 access control rule for vdc ' + vdc_name)
        control_access = vdc.remove_access_settings(
            access_settings_list=[{
                'name': vapp_user_name,
                'type': 'user'
            }])
        self.assertEqual(len(control_access.AccessSettings.AccessSetting), 1)

        # share
        logger.debug('Sharing vdc ' + vdc_name + ' with everyone in the org')
        vdc.reload()
        control_access = vdc.share_with_org_members()
        self.assertEqual(control_access.IsSharedToEveryone.text, 'true')
        self.assertEqual(control_access.EveryoneAccessLevel.text, 'ReadOnly')

        # unshare
        logger.debug(
            'Un-sharing vdc ' + vdc_name + ' from everyone in the org')
        vdc.reload()
        control_access = vdc.unshare_from_org_members()
        self.assertEqual(control_access.IsSharedToEveryone.text, 'false')

        # remove the last access setting
        logger.debug('Removing the last remaining access control from'
                     ' vdc ' + vdc_name)
        vdc.reload()
        control_access = vdc.remove_access_settings(remove_all=True)
        self.assertFalse(hasattr(control_access, 'AccessSettings'))

    @developerModeAware
    def test_9998_teardown(self):
        """Test the method VDC.delete_vdc().

        Invoke the method for the vdc created by setup.

        This test passes if the task for deleting the vdc succeeds.
        """
        logger = Environment.get_default_logger()
        vdc = VDC(TestOrgVDC._client, href=TestOrgVDC._new_vdc_href)
        # Disable the org vdc before deleting it. In case the org vdc is
        # already disabled, we don't want the exception to leak out.
        try:
            vdc.enable_vdc(enable=False)
            logger.debug('Disabled vdc ' + TestOrgVDC._new_vdc_name + '.')
        except OperationNotSupportedException as e:
            logger.debug('vdc ' + TestOrgVDC._new_vdc_name +
                         ' is already disabled.')
            pass
        task = vdc.delete_vdc()
        TestOrgVDC._client.get_task_monitor().wait_for_success(task=task)
        logger.debug('Deleted vdc ' + TestOrgVDC._new_vdc_name + '.')

    def test_9999_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestOrgVDC._client.logout()
