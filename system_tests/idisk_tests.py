import unittest

from pyvcloud.system_test_framework.base_test import BaseTestCase
from pyvcloud.system_test_framework.environment import CommonRoles
from pyvcloud.system_test_framework.environment import developerModeAware
from pyvcloud.system_test_framework.environment import Environment

from pyvcloud.vcd.client import TaskStatus


class TestDisk(BaseTestCase):
    """Test independent disk functionalities implemented in pyvcloud."""

    _client = None

    _idisk1_name = 'test_idisk'
    _idisk1_size = '10'
    _idisk1_description = 'First disk'
    _idisk1_id = None
    _idisk1_new_name = 'test_idisk_new'
    _idisk1_new_size = '20'
    _idisk1_new_description = 'New description of first disk'

    _idisk2_name = 'test_idisk_2'
    _idisk2_size = '20'
    _idisk2_description = 'Second disk'
    _idisk2_id = None

    _idisk3_name = 'test_idisk_2'
    _idisk3_size = '30'
    _idisk3_description = 'Third disk namesake of Second disk'
    _idisk3_id = None

    def test_0000_setup(self):
        """Setup the independent disks for the other tests in this module.

        Create three independent disks as per the configuration stated
            above. In case the disks exist, re-use them.

        This test passes if all the three disk ids are not None.
        """
        logger = Environment.get_default_logger()
        TestDisk._client = Environment.get_client_in_default_org(
            CommonRoles.CATALOG_AUTHOR)
        vdc = Environment.get_test_vdc(TestDisk._client)

        disks = vdc.get_disks()
        for disk in disks:
            if TestDisk._idisk1_id is None and disk.get('name').lower() \
               == self._idisk1_name:
                logger.debug('Reusing ' + TestDisk._idisk1_name)
                TestDisk._idisk1_id = disk.get('id')[16:]
            elif TestDisk._idisk2_id is None and disk.get('name').lower() \
              == self._idisk2_name and str(disk.Description).lower() \
              == self._idisk2_description.lower(): # NOQA
                logger.debug('Reusing ' + TestDisk._idisk2_name)
                TestDisk._idisk2_id = disk.get('id')[16:]
            elif TestDisk._idisk3_id is None and disk.get('name').lower() \
              == self._idisk3_name: # NOQA
                logger.debug('Reusing ' + TestDisk._idisk3_name)
                TestDisk._idisk3_id = disk.get('id')[16:]

        if TestDisk._idisk1_id is None:
            TestDisk._idisk1_id = self._create_disk_helper(
                client=TestDisk._client,
                vdc=vdc,
                disk_name=self._idisk1_name,
                disk_size=self._idisk1_size,
                disk_description=self._idisk1_description)

        if TestDisk._idisk2_id is None:
            TestDisk._idisk2_id = self._create_disk_helper(
                client=TestDisk._client,
                vdc=vdc,
                disk_name=self._idisk2_name,
                disk_size=self._idisk2_size,
                disk_description=self._idisk2_description)

        if TestDisk._idisk3_id is None:
            TestDisk._idisk3_id = self._create_disk_helper(
                client=TestDisk._client,
                vdc=vdc,
                disk_name=self._idisk3_name,
                disk_size=self._idisk3_size,
                disk_description=self._idisk3_description)

        self.assertIsNotNone(TestDisk._idisk1_id)
        self.assertIsNotNone(TestDisk._idisk2_id)
        self.assertIsNotNone(TestDisk._idisk3_id)

    def _create_disk_helper(self, client, vdc, disk_name, disk_size,
                            disk_description):
        logger = Environment.get_default_logger()
        logger.debug('Creating disk : ' + disk_name)
        disk_sparse = vdc.create_disk(
            name=disk_name, size=disk_size, description=disk_description)

        task = client.get_task_monitor().wait_for_success(
            disk_sparse.Tasks.Task[0])

        self.assertEqual(task.get('status'), TaskStatus.SUCCESS.value)
        disk_id = disk_sparse.get('id')[16:]
        logger.debug('Created disk with id:' + disk_id)
        return disk_id

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

        This test passes if the disk returned by the method is nor None,
            and it's name matches the expected name of the disk.
        """
        vdc = Environment.get_test_vdc(TestDisk._client)

        fetched_disk = vdc.get_disk(name=self._idisk1_name)

        self.assertIsNotNone(fetched_disk)
        self.assertEqual(fetched_disk.get('name'), self._idisk1_name)

    def test_0030_get_disk_by_id(self):
        """Test the  method vdc.get_disk() called with 'id' param.

        Invoke the method with the id of the second independent disk.

        This test passes if the disk returned by the method is nor None,
            and it's id matches the expected id of the disk.
        """
        vdc = Environment.get_test_vdc(TestDisk._client)

        fetched_disk = vdc.get_disk(disk_id=TestDisk._idisk2_id)
        self.assertIsNotNone(fetched_disk)
        self.assertEqual(fetched_disk.get('name'), self._idisk2_name)

    def test_0040_change_idisk_owner(self):
        """Test the  method vdc.change_disk_owner().

        Invoke the method for the third independent disk, to make vapp_user
            the owner of the disk. Revert back teh ownership to catalog_author
            once the test is over.

        This test passes if the disk states it's owner as vapp_user after
            the method call.
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

            # Revert ownership to catalog author
            username = Environment.get_username_for_role_in_test_org(
                CommonRoles.CATALOG_AUTHOR)
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

        Invoke the method for the second independent disk, to attach it to
            the default test vm available in the Environment.

        This test passes if the disk attachment task succeeds.
        """
        org_admin_client = Environment.get_client_in_default_org(
            CommonRoles.ORGANIZATION_ADMINISTRATOR)
        vdc = Environment.get_test_vdc(org_admin_client)
        vapp = Environment.get_default_vapp(org_admin_client)
        vm_name = Environment.get_default_vm_name()
        disk = vdc.get_disk(disk_id=TestDisk._idisk2_id)

        try:
            result = vapp.attach_disk_to_vm(
                disk_href=disk.get('href'), vm_name=vm_name)
            task = org_admin_client.get_task_monitor().wait_for_success(
                task=result)
            self.assertEqual(task.get('status'), TaskStatus.SUCCESS.value)
        finally:
            org_admin_client.logout()

    def test_0060_detach_disk_from_vm_in_vapp(self):
        """Test the  method vapp.detach_disk_to_vm().

        Invoke the method for the second independent disk, to detach it from
            the default test vm available in the Environment. we need to power
            down the vm before running this test, and power it back on once the
            test is over.

        This test passes if the disk detachment task succeeds.
        """
        org_admin_client = Environment.get_client_in_default_org(
            CommonRoles.ORGANIZATION_ADMINISTRATOR)
        vdc = Environment.get_test_vdc(org_admin_client)
        vapp = Environment.get_default_vapp(org_admin_client)
        vm_name = Environment.get_default_vm_name()
        disk = vdc.get_disk(disk_id=TestDisk._idisk2_id)

        try:
            # vm needs to be powered off for detach to succeed.
            self._power_off_vapp(org_admin_client, vapp)

            vapp.reload()
            result = vapp.detach_disk_from_vm(
                disk_href=disk.get('href'), vm_name=vm_name)
            task = org_admin_client.get_task_monitor().wait_for_success(
                task=result)
            self.assertEqual(task.get('status'), TaskStatus.SUCCESS.value)

            vapp.reload()
            # power on vapp, once detaching disk is successful, for sanity of
            # next test run.
            self._power_on_vapp(org_admin_client, vapp)
        finally:
            org_admin_client.logout()

    def _power_off_vapp(self, org_admin_client, vapp):
        # TODO(VCDA-603) : update power_off to handle missing link exception
        try:
            task = vapp.power_off()
            org_admin_client.get_task_monitor().wait_for_success(task=task)
        except Exception as e:
            pass

    def _power_on_vapp(self, org_admin_client, vapp):
        # TODO(VCDA-603) : update power_on to handle missing link exception
        try:
            task = vapp.power_on()
            org_admin_client.get_task_monitor().wait_for_success(task=task)
        except Exception as e:
            pass

    def test_0070_update_disk(self):
        """Test the  method vapp.update_disk().

        Invoke the method for the first independent disk, to update it's
            name, size and description. Revert the changes back once the test
            is over.

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

        # return disk 1 to original state
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
        """Test the  method vapp.delete_disk().

        Invoke the method for all the disks created by setup.

        This test passes if all the tasks for deleting the disks succeed.
        """
        disks_to_delete = [
            TestDisk._idisk1_id, TestDisk._idisk2_id, TestDisk._idisk3_id
        ]
        org_admin_client = Environment.get_client_in_default_org(
            CommonRoles.ORGANIZATION_ADMINISTRATOR)
        vdc = Environment.get_test_vdc(org_admin_client)

        try:
            for disk_id in disks_to_delete:
                if disk_id is not None:
                    task = vdc.delete_disk(disk_id=disk_id)
                    org_admin_client.get_task_monitor()\
                        .wait_for_success(task=task)
                    vdc.reload()
        finally:
            org_admin_client.logout()

    def test_9999_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestDisk._client.logout()


if __name__ == '__main__':
    unittest.main()
