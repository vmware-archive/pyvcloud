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
from pyvcloud.system_test_framework.environment import developerModeAware
from pyvcloud.system_test_framework.environment import Environment

from pyvcloud.vcd.exceptions import EntityNotFoundException
from pyvcloud.vcd.exceptions import OperationNotSupportedException
from pyvcloud.vcd.vdc import VDC


class TestOrgVDC(BaseTestCase):
    """Test OrgVDC functionalities implemented in pyvcloud."""

    _client = None

    _new_vdc_name = 'test_org_vdc_' + str(uuid1())
    _new_vdc_href = None
    _non_existent_vdc_name = 'non_existent_vdc_' + str(uuid1())

    def test_0000_setup(self):
        """Setup the vApps required for the other tests in this module.

        Create two vApps as per the configuration stated above. In case the
        vApps exist, re-use them.

        This test passes if the two vApp hrefs are not None.
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

        logger.debug('Creating ovdc ' + vdc_name + '.')
        vdc_resource = org.create_org_vdc(
            vdc_name,
            pvdc_name,
            storage_profiles=storage_profiles,
            uses_fast_provisioning=True,
            is_thin_provision=True)

        TestOrgVDC._client.get_task_monitor().wait_for_success(
            task=vdc_resource.Tasks.Task[0])

        org.reload()
        # The following contraption is required to get the non admin href of
        # the ovdc. vdc_resource contains the admin version of the href since
        # we created the ovdc as a sys admin.
        for vdc in org.list_vdcs():
            if vdc.get('name').lower() == vdc_name.lower():
                TestOrgVDC._new_vdc_href = vdc.get('href')

        self.assertIsNotNone(TestOrgVDC._new_vdc_href)

    def test_0010_list_vdc(self):
        """."""
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
        """."""
        org = Environment.get_test_org(TestOrgVDC._client)
        vdc = org.get_vdc(TestOrgVDC._new_vdc_name)

        self.assertEqual(TestOrgVDC._new_vdc_name, vdc.get('name'))
        self.assertEqual(TestOrgVDC._new_vdc_href, vdc.get('href'))

    def test_0030_get_non_existent_vdc(self):
        """."""
        org = Environment.get_test_org(TestOrgVDC._client)
        try:
            org.get_vdc(TestOrgVDC._non_existent_vdc_name)
            self.fail('Should not be able to fetch vdc ' +
                      TestOrgVDC._non_existent_vdc_name)
        except EntityNotFoundException as e:
            pass

    def test_0040_enable_disable_vdc(self):
        """."""
        vdc = VDC(TestOrgVDC._client, href=TestOrgVDC._new_vdc_href)
        # vdc should be in enabled state after the previous tests.

        # disable the vdc
        vdc.enable_vdc(enable=False)
        # try to disbale a disabled org vdc. Operation should fail.
        try:
            vdc.enable_vdc(enable=False)
            self.fail('Should not be able to disable vdc ' +
                      TestOrgVDC._new_vdc_href)
        except OperationNotSupportedException as e:
            pass

        # enable the vdc
        vdc.enable_vdc(enable=True)
        # try to enable an already enabled org vdc. Operation should fail.
        try:
            vdc.enable_vdc(enable=True)
            self.fail('Should not be able to enable vdc ' +
                      TestOrgVDC._new_vdc_href)
        except OperationNotSupportedException as e:
            pass

    def test_0050_vdc_acl(self):
        """."""
        pass

    @developerModeAware
    def test_9998_teardown(self):
        """Test the  method vdc.delete_vdc().

        Invoke the method for the vdc created by setup.

        This test passes if the task for deleting the vdc succeeds.
        """
        vdc = VDC(TestOrgVDC._client, href=TestOrgVDC._new_vdc_href)
        # Disable the org vdc before deleting it. In case the org vdc is
        # already disabled, we don't want the exception to leak out.
        try:
            vdc.enable_vdc(enable=False)
        except OperationNotSupportedException as e:
            pass
        task = vdc.delete_vdc()
        TestOrgVDC._client.get_task_monitor().wait_for_success(task=task)

    def test_9999_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestOrgVDC._client.logout()
