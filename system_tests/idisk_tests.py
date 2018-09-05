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
from pyvcloud.system_test_framework.environment import CommonRoles
from pyvcloud.system_test_framework.environment import developerModeAware
from pyvcloud.system_test_framework.environment import Environment
from pyvcloud.system_test_framework.utils import \
    create_customized_vapp_from_template
from pyvcloud.system_test_framework.utils import create_independent_disk

from pyvcloud.vcd.client import NetworkAdapterType
from pyvcloud.vcd.client import TaskStatus
from pyvcloud.vcd.vapp import VApp


class TestDisk(BaseTestCase):
    """Test independent disk functionalities implemented in pyvcloud."""

    _test_runner_role = CommonRoles.VAPP_AUTHOR
    _client = None

    _idisk1_name = 'test_idisk_' + str(uuid1())
    _idisk1_size = '10'
    _idisk1_description = 'First disk'
    _idisk1_id = None
    _idisk1_new_name = 'test_idisk_new_name_' + str(uuid1())
    _idisk1_new_size = '20'
    _idisk1_new_description = 'New description of first disk'

    _idisk2_name = 'test_idisk_' + str(uuid1())
    _idisk2_size = '20'
    _idisk2_description = 'Second disk'
    _idisk2_id = None

    _idisk3_name = _idisk2_name
    _idisk3_size = '30'
    _idisk3_description = 'Third disk, namesake of second disk'
    _idisk3_id = None

    _test_vapp_name = 'test_vApp_' + str(uuid1())
    _test_vapp_first_vm_num_cpu = 2
    _test_vapp_first_vm_new_num_cpu = 4
    _test_vapp_first_vm_memory_size = 64  # MB
    _test_vapp_first_vm_new_memory_size = 128  # MB
    _test_vapp_first_vm_first_disk_size = 100  # MB
    _test_vapp_first_vm_name = 'first-vm'
    _test_vapp_first_vm_network_adapter_type = NetworkAdapterType.VMXNET3
    _test_vapp_href = None

    def test_0000_setup(self):
        """Setup the independent disks for the other tests in this module.

        Create three independent disks as per the configuration stated above.
        Also create a vApp that will be used in attach/detach independent disk
        tests.

        This test passes if all the three disk ids and the vapp href are not
        None.
        """
        logger = Environment.get_default_logger()
        TestDisk._client = Environment.get_client_in_default_org(
            TestDisk._test_runner_role)
        vdc = Environment.get_test_vdc(TestDisk._client)

        logger.debug('Creating disk : ' + TestDisk._idisk1_name)
        TestDisk._idisk1_id = create_independent_disk(
            client=TestDisk._client,
            vdc=vdc,
            name=TestDisk._idisk1_name,
            size=TestDisk._idisk1_size,
            description=TestDisk._idisk1_description)

        logger.debug('Creating disk : ' + TestDisk._idisk2_name)
        TestDisk._idisk2_id = create_independent_disk(
            client=TestDisk._client,
            vdc=vdc,
            name=TestDisk._idisk2_name,
            size=TestDisk._idisk2_size,
            description=TestDisk._idisk2_description)

        logger.debug('Creating disk : ' + TestDisk._idisk3_name)
        TestDisk._idisk3_id = create_independent_disk(
            client=TestDisk._client,
            vdc=vdc,
            name=TestDisk._idisk3_name,
            size=TestDisk._idisk3_size,
            description=TestDisk._idisk3_description)

        logger.debug('Creating vApp ' + TestDisk._test_vapp_name + '.')
        TestDisk._test_vapp_href = create_customized_vapp_from_template(
            client=TestDisk._client,
            vdc=vdc,
            name=TestDisk._test_vapp_name,
            catalog_name=Environment.get_default_catalog_name(),
            template_name=Environment.get_default_template_name(),
            memory_size=TestDisk._test_vapp_first_vm_memory_size,
            num_cpu=TestDisk._test_vapp_first_vm_num_cpu,
            disk_size=TestDisk._test_vapp_first_vm_first_disk_size,
            vm_name=TestDisk._test_vapp_first_vm_name,
            nw_adapter_type=TestDisk._test_vapp_first_vm_network_adapter_type)

        self.assertIsNotNone(TestDisk._idisk1_id)
        self.assertIsNotNone(TestDisk._idisk2_id)
        self.assertIsNotNone(TestDisk._idisk3_id)
        self.assertIsNotNone(TestDisk._test_vapp_href)

    def test_0010_get_all_disks(self):
        """Test the  method vdc.get_disks().

        This test passes if all the expected disk names are in the list of
        disk returned by vdc.det_disks()
        """
        vdc = Environment.get_test_vdc(TestDisk._client)
        disks = vdc.get_disks()

        self.assertTrue(len(disks) > 0)
        disk_names = []
        for disk in disks:
            disk_names.append(disk.get('name'))

        expected_names = [
            self._idisk1_name, self._idisk2_name, self._idisk3_name
        ]

        for name in expected_names:
            self.assertIn(name, disk_names)

    def test_0020_get_disk_by_name(self):
        """Test the  method vdc.get_disk() called with 'name' param.

        Invoke the method with the name of the first independent disk.

        This test passes if the disk returned by the method is nor None, and
        its name matches the expected name of the disk.
        """
        vdc = Environment.get_test_vdc(TestDisk._client)

        fetched_disk = vdc.get_disk(name=self._idisk1_name)

        self.assertIsNotNone(fetched_disk)
        self.assertEqual(fetched_disk.get('name'), self._idisk1_name)

    def test_0030_get_disk_by_id(self):
        """Test the  method vdc.get_disk() called with 'id' param.

        Invoke the method with the id of the second independent disk.

        This test passes if the disk returned by the method is nor None, and
        its id matches the expected id of the disk.
        """
        vdc = Environment.get_test_vdc(TestDisk._client)

        fetched_disk = vdc.get_disk(disk_id=TestDisk._idisk2_id)
        self.assertIsNotNone(fetched_disk)
        self.assertEqual(fetched_disk.get('name'), self._idisk2_name)

    def test_0040_change_idisk_owner(self):
        """Test the  method vdc.change_disk_owner().

        Invoke the method for the third independent disk, to make vapp_user the
        owner of the disk. Revert back the ownership to the original owner once
        the test is over.

        This test passes if the disk states its owner as vapp_user after the
        method call.
        """
        org_admin_client = Environment.get_client_in_default_org(
            CommonRoles.ORGANIZATION_ADMINISTRATOR)
        org = Environment.get_test_org(org_admin_client)
        vdc = Environment.get_test_vdc(org_admin_client)

        try:
            username = Environment.get_username_for_role_in_test_org(
                CommonRoles.VAPP_USER)
            user_resource = org.get_user(username)

            vdc.change_disk_owner(
                disk_id=TestDisk._idisk3_id,
                user_href=user_resource.get('href'))

            disk_resource = vdc.get_disk(disk_id=TestDisk._idisk3_id)
            new_owner_name = disk_resource.Owner.User.get('name')
            self.assertEqual(new_owner_name, username)

            # Revert ownership to original owner
            username = Environment.get_username_for_role_in_test_org(
                TestDisk._test_runner_role)
            user_resource = org.get_user(username)

            vdc.change_disk_owner(
                disk_id=TestDisk._idisk3_id,
                user_href=user_resource.get('href'))

            disk_resource = vdc.get_disk(disk_id=TestDisk._idisk3_id)
            new_owner_name = disk_resource.Owner.User.get('name')
            self.assertEqual(new_owner_name, username)
        finally:
            org_admin_client.logout()

    def test_0050_attach_disk_to_vm_in_vapp(self):
        """Test the  method vapp.attach_disk_to_vm().

        Invoke the method for the second independent disk, and attach it to the
        first vm in the vApp created during setup. The vApp must be in deployed
        state before we try to attach the disk to it.

        This test passes if the disk attachment task succeeds.
        """
        vdc = Environment.get_test_vdc(TestDisk._client)
        vapp = VApp(TestDisk._client, href=TestDisk._test_vapp_href)
        vm_name = TestDisk._test_vapp_first_vm_name
        disk = vdc.get_disk(disk_id=TestDisk._idisk2_id)

        # vApp needs to be deployed for attach to succeed.
        if vapp.is_suspended():
            task = vapp.deploy()
            TestDisk._client.get_task_monitor().wait_for_success(task=task)

        task = vapp.attach_disk_to_vm(
            disk_href=disk.get('href'), vm_name=vm_name)
        TestDisk._client.get_task_monitor().wait_for_success(
            task=task)

    def test_0060_detach_disk_from_vm_in_vapp(self):
        """Test the  method vapp.detach_disk_to_vm().

        Invoke the method for the second independent disk, detach it from the
        first vm of the vApp created during setup. We need to power down the
        vm before running this test, and power it back on once the test
        is over.

        This test passes if the disk detachment task succeeds.
        """
        vdc = Environment.get_test_vdc(TestDisk._client)
        vapp = VApp(TestDisk._client, href=TestDisk._test_vapp_href)
        vm_name = TestDisk._test_vapp_first_vm_name
        disk = vdc.get_disk(disk_id=TestDisk._idisk2_id)

        # vm needs to be powered off for detach to succeed.
        is_vapp_powered_on_before_test = vapp.is_powered_on()
        if is_vapp_powered_on_before_test:
            task = vapp.power_off()
            TestDisk._client.get_task_monitor().wait_for_success(task=task)

        vapp.reload()
        task = vapp.detach_disk_from_vm(
            disk_href=disk.get('href'), vm_name=vm_name)
        TestDisk._client.get_task_monitor().wait_for_success(task=task)

        vapp.reload()
        # restore vApp to powered on state (if required)
        if is_vapp_powered_on_before_test:
            task = vapp.power_on()
            TestDisk._client.get_task_monitor().wait_for_success(task=task)

    def test_0070_update_disk(self):
        """Test the  method vapp.update_disk().

        Invoke the method for the first independent disk, to update its name,
        size and description. Revert the changes back once the test is over.

        This test passes if the updated disk's name, size and description
        matches the expected values.
        """
        vdc = Environment.get_test_vdc(TestDisk._client)

        result = vdc.update_disk(
            name=self._idisk1_name,
            new_name=self._idisk1_new_name,
            new_size=self._idisk1_new_size,
            new_description=self._idisk1_new_description)

        task = TestDisk._client.get_task_monitor().wait_for_success(
            task=result)
        self.assertEqual(task.get('status'), TaskStatus.SUCCESS.value)

        disk = vdc.get_disk(name=self._idisk1_new_name)
        self.assertIsNotNone(disk)
        self.assertEqual(disk.get('size'), str(self._idisk1_new_size))
        self.assertEqual(disk.Description, self._idisk1_new_description)

        # return disk1 to original state
        result = vdc.update_disk(
            name=self._idisk1_new_name,
            new_name=self._idisk1_name,
            new_size=self._idisk1_size,
            new_description=self._idisk1_description)

        task = TestDisk._client.get_task_monitor().wait_for_success(
            task=result)
        self.assertEqual(task.get('status'), TaskStatus.SUCCESS.value)

    @developerModeAware
    def test_9998_teardown(self):
        """Test the method vapp.delete_disk().

        Invoke the method for all the disks created by setup. Also delete the
        vApp created suring setup.

        This test passes if all the tasks for deleting the disks and vApp
        succeed.
        """
        org_admin_client = Environment.get_client_in_default_org(
            CommonRoles.ORGANIZATION_ADMINISTRATOR)
        vdc = Environment.get_test_vdc(org_admin_client)

        try:
            disks_to_delete = [
                TestDisk._idisk1_id, TestDisk._idisk2_id, TestDisk._idisk3_id
            ]
            for disk_id in disks_to_delete:
                if disk_id is not None:
                    vdc.reload()
                    task = vdc.delete_disk(disk_id=disk_id)
                    org_admin_client.get_task_monitor()\
                        .wait_for_success(task=task)

            task = vdc.delete_vapp(name=TestDisk._test_vapp_name, force=True)
            org_admin_client.get_task_monitor().wait_for_success(task)
        finally:
            org_admin_client.logout()

    def test_9999_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestDisk._client.logout()


if __name__ == '__main__':
    unittest.main()
