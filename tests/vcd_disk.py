# VMware vCloud Director Python SDK
# Copyright (c) 2014-2018 VMware, Inc. All Rights Reserved.
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

from pyvcloud.vcd.client import TaskStatus
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.test import TestCase
from pyvcloud.vcd.vapp import VApp
from pyvcloud.vcd.vdc import VDC


class TestDisk(TestCase):
    def test_010_create_disk(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=vdc_resource)

        result = vdc.create_disk(
            name=self.config['vcd']['idisk_name'],
            size=self.config['vcd']['idisk_size'],
            description=self.config['vcd']['idisk_description'])

        task = self.client.get_task_monitor().wait_for_status(
            task=result.Tasks.Task[0],
            timeout=30,
            poll_frequency=2,
            fail_on_status=None,
            expected_target_statuses=[
                TaskStatus.SUCCESS, TaskStatus.ABORTED, TaskStatus.ERROR,
                TaskStatus.CANCELED
            ],
            callback=None)

        assert task.get('status') == TaskStatus.SUCCESS.value

    def test_020_get_all_disks(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=vdc_resource)

        disks = vdc.get_disks()

        assert len(disks) > 0
        assert disks[0].get('name') == self.config['vcd']['idisk_name']

    def test_030_get_disk_by_name(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=vdc_resource)

        fetched_disk = vdc.get_disk(name=self.config['vcd']['idisk_name'])

        assert fetched_disk is not None
        assert fetched_disk.get('name') == self.config['vcd']['idisk_name']

    def test_040_get_disk_by_id(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=vdc_resource)

        disks = vdc.get_disks()
        assert len(disks) > 0

        fetched_disk = vdc.get_disk(disk_id=disks[0].get('id'))
        assert fetched_disk is not None

    def test_050_change_idisk_owner(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=vdc_resource)

        user_resource = org.get_user(
            self.config['vcd']['idisk_new_owner_name'])

        vdc.change_disk_owner(name=self.config['vcd']['idisk_name'],
                              user_href=user_resource.get('href'))

        disk_resource = vdc.get_disk(self.config['vcd']['idisk_name'])
        new_user = disk_resource.Owner.User.get('name')

        assert self.config['vcd']['idisk_new_owner_name'] == new_user

    def test_060_attach_disk_to_vm_in_vapp(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=vdc_resource)
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')

        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        assert self.config['vcd']['vapp'] == vapp_resource.get('name')
        vapp = VApp(self.client, resource=vapp_resource)

        disk = vdc.get_disk(self.config['vcd']['idisk_name'])

        result = vapp.attach_disk_to_vm(disk_href=disk.get('href'),
                                        vm_name=self.config['vcd']['vm'])
        task = self.client.get_task_monitor().wait_for_status(
                            task=result,
                            timeout=60,
                            poll_frequency=2,
                            fail_on_statuses=None,
                            expected_target_statuses=[
                                TaskStatus.SUCCESS,
                                TaskStatus.ABORTED,
                                TaskStatus.ERROR,
                                TaskStatus.CANCELED],
                            callback=None)
        assert task.get('status') == TaskStatus.SUCCESS.value

    def test_070_detach_disk_from_vm_in_vapp(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=vdc_resource)
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')

        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        assert self.config['vcd']['vapp'] == vapp_resource.get('name')
        vapp = VApp(self.client, resource=vapp_resource)

        disk = vdc.get_disk(self.config['vcd']['idisk_name'])

        result = vapp.detach_disk_from_vm(disk_href=disk.get('href'),
                                          vm_name=self.config['vcd']['vm'])
        task = self.client.get_task_monitor().wait_for_status(
                            task=result,
                            timeout=60,
                            poll_frequency=2,
                            fail_on_statuses=None,
                            expected_target_statuses=[
                                TaskStatus.SUCCESS,
                                TaskStatus.ABORTED,
                                TaskStatus.ERROR,
                                TaskStatus.CANCELED],
                            callback=None)
        assert task.get('status') == TaskStatus.SUCCESS.value

    def test_080_update_disk(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=vdc_resource)

        result = vdc.update_disk(
            name=self.config['vcd']['idisk_name'],
            new_name=self.config['vcd']['idisk_new_name'],
            new_size=self.config['vcd']['idisk_new_size'],
            new_description=self.config['vcd']['idisk_new_description'],
            new_storage_profile_name=self.config['vcd']['idisk_new_sp_name'],
            new_iops=self.config['vcd']['idisk_new_iops'])

        task = self.client.get_task_monitor().wait_for_status(
            task=result,
            timeout=30,
            poll_frequency=2,
            fail_on_statuses=None,
            expected_target_statuses=[
                TaskStatus.SUCCESS, TaskStatus.ABORTED, TaskStatus.ERROR,
                TaskStatus.CANCELED
            ],
            callback=None)

        assert task.get('status') == TaskStatus.SUCCESS.value

    def test_200_delete_all_disks(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=vdc_resource)

        disks = vdc.get_disks()

        for disk in disks:
            result = vdc.delete_disk(disk_id=disk.get('id'))

            task = self.client.get_task_monitor().wait_for_status(
                task=result,
                timeout=30,
                poll_frequency=2,
                fail_on_status=None,
                expected_target_statuses=[
                    TaskStatus.SUCCESS, TaskStatus.ABORTED, TaskStatus.ERROR,
                    TaskStatus.CANCELED
                ],
                callback=None)
            assert task.get('status') == TaskStatus.SUCCESS.value


if __name__ == '__main__':
    unittest.main()
