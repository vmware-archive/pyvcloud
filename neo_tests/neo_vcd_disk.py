import unittest

from neo_tests.base_test import BaseTestCase
from neo_tests.environment import CommonRoles
from neo_tests.environment import Environment
from neo_tests.environment import developerModeAware

from pyvcloud.vcd.client import TaskStatus


class TestDisk(BaseTestCase):
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
        TestDisk._client = Environment.get_client(CommonRoles.CATALOG_AUTHOR)
        vdc = Environment.get_default_vdc(TestDisk._client)

        TestDisk._idisk1_id = self._create_disk_helper(
            client=TestDisk._client,
            vdc=vdc,
            disk_name=self._idisk1_name,
            disk_size=self._idisk1_size,
            disk_description=self._idisk1_description)

        TestDisk._idisk2_id = self._create_disk_helper(
            client=TestDisk._client,
            vdc=vdc,
            disk_name=self._idisk2_name,
            disk_size=self._idisk2_size,
            disk_description=self._idisk2_description)

        TestDisk._idisk3_id = self._create_disk_helper(
            client=TestDisk._client,
            vdc=vdc,
            disk_name=self._idisk3_name,
            disk_size=self._idisk3_size,
            disk_description=self._idisk3_description)

    def _create_disk_helper(self, client, vdc, disk_name, disk_size,
                            disk_description):
        print('Creating disk : ' + disk_name)
        disk_sparse = vdc.create_disk(
            name=disk_name,
            size=disk_size,
            description=disk_description)

        task = client.get_task_monitor().wait_for_success(
            disk_sparse.Tasks.Task[0])

        self.assertEqual(task.get('status'), TaskStatus.SUCCESS.value)
        disk_id = disk_sparse.get('id')[16:]
        print('Created disk with id:' + disk_id)
        return disk_id

    def test_0010_get_all_disks(self):
        vdc = Environment.get_default_vdc(TestDisk._client)
        disks = vdc.get_disks()

        self.assertTrue(len(disks) > 0)
        expected_names = {self._idisk1_name,
                          self._idisk2_name,
                          self._idisk3_name}
        self.assertIn(disks[0].get('name'), expected_names)
        self.assertIn(disks[1].get('name'), expected_names)
        self.assertIn(disks[2].get('name'), expected_names)

    def test_0020_get_disk_by_name(self):
        vdc = Environment.get_default_vdc(TestDisk._client)

        fetched_disk = vdc.get_disk(name=self._idisk1_name)

        self.assertIsNotNone(fetched_disk)
        self.assertEqual(fetched_disk.get('name'), self._idisk1_name)

    def test_0030_get_disk_by_id(self):
        vdc = Environment.get_default_vdc(TestDisk._client)

        fetched_disk = vdc.get_disk(disk_id=TestDisk._idisk2_id)
        self.assertIsNotNone(fetched_disk)
        self.assertEqual(fetched_disk.get('name'), self._idisk2_name)

    def test_0040_change_idisk_owner(self):
        org_admin_client = Environment.get_client(
            CommonRoles.ORGANIZATION_ADMINISTRATOR)
        org = Environment.get_default_org(org_admin_client)
        vdc = Environment.get_default_vdc(org_admin_client)

        new_username = Environment.get_default_username_for_role(
            CommonRoles.VAPP_USER)
        user_resource = org.get_user(new_username)

        vdc.change_disk_owner(disk_id=TestDisk._idisk3_id,
                              user_href=user_resource.get('href'))

        disk_resource = vdc.get_disk(disk_id=TestDisk._idisk3_id)
        new_owner_name = disk_resource.Owner.User.get('name')

        org_admin_client.logout()

        self.assertEqual(new_owner_name, new_username)

    def test_0049_attach_detach_setup(self):
        # vm needs to be powered off for detach to succeed
        org_admin_client = Environment.get_client(
            CommonRoles.ORGANIZATION_ADMINISTRATOR)
        vapp = Environment.get_default_vapp(org_admin_client)

        # TODO : update power_off to handle missing link exception
        try:
            task = vapp.power_off()
            org_admin_client.get_task_monitor().wait_for_success(
                task=task)
            org_admin_client.logout()
        except Exception as e:
            pass

    def test_0050_attach_disk_to_vm_in_vapp(self):
        org_admin_client = Environment.get_client(
            CommonRoles.ORGANIZATION_ADMINISTRATOR)
        vdc = Environment.get_default_vdc(org_admin_client)
        vapp = Environment.get_default_vapp(org_admin_client)
        vm_name = Environment.get_default_vm_name()
        disk = vdc.get_disk(disk_id=TestDisk._idisk2_id)

        result = vapp.attach_disk_to_vm(disk_href=disk.get('href'),
                                        vm_name=vm_name)
        task = org_admin_client.get_task_monitor().wait_for_success(
            task=result)
        org_admin_client.logout()
        self.assertEqual(task.get('status'), TaskStatus.SUCCESS.value)

    def test_0060_detach_disk_from_vm_in_vapp(self):
        org_admin_client = Environment.get_client(
            CommonRoles.ORGANIZATION_ADMINISTRATOR)
        vdc = Environment.get_default_vdc(org_admin_client)
        vapp = Environment.get_default_vapp(org_admin_client)
        vm_name = Environment.get_default_vm_name()
        disk = vdc.get_disk(disk_id=TestDisk._idisk2_id)

        result = vapp.detach_disk_from_vm(disk_href=disk.get('href'),
                                          vm_name=vm_name)
        task = org_admin_client.get_task_monitor().wait_for_success(
            task=result)
        org_admin_client.logout()
        self.assertEqual(task.get('status'), TaskStatus.SUCCESS.value)

    def test_0070_update_disk(self):
        vdc = Environment.get_default_vdc(TestDisk._client)

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

        # return disk 1 to original name
        result = vdc.update_disk(
            name=self._idisk1_new_name,
            new_name=self._idisk1_name,
            new_size=self._idisk1_size,
            new_description=self._idisk1_description)

        task = TestDisk._client.get_task_monitor().wait_for_success(
            task=result)
        self.assertEqual(task.get('status'), TaskStatus.SUCCESS.value)

    @developerModeAware
    def test_9999_teardown(self):
        TestDisk._client.logout()

        disks_to_delete = [TestDisk._idisk1_id,
                           TestDisk._idisk2_id,
                           TestDisk._idisk3_id]
        org_admin_client = Environment.get_client(
            CommonRoles.ORGANIZATION_ADMINISTRATOR)
        for disk_id in disks_to_delete:
            vdc = Environment.get_default_vdc(org_admin_client)

            task = vdc.delete_disk(disk_id=disk_id)
            org_admin_client.get_task_monitor().wait_for_success(task=task)

        org_admin_client.logout()


if __name__ == '__main__':
    unittest.main()
