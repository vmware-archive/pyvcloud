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

from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import TaskStatus
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.test import TestCase
from pyvcloud.vcd.vapp import VApp
from pyvcloud.vcd.vdc import VDC


class TestVApp(TestCase):
    def test_001_instantiate_vapp(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        result = vdc.instantiate_vapp(
            self.config['vcd']['vapp'],
            self.config['vcd']['catalog'],
            self.config['vcd']['template'],
            network='net2',
            fence_mode='natRouted',
            deploy=False,
            power_on=False)
        task = self.client.get_task_monitor().wait_for_status(
            task=result.Tasks.Task[0],
            timeout=60,
            poll_frequency=2,
            fail_on_statuses=None,
            expected_target_statuses=[
                TaskStatus.SUCCESS, TaskStatus.ABORTED, TaskStatus.ERROR,
                TaskStatus.CANCELED
            ],
            callback=None)
        assert task.get('status') == TaskStatus.SUCCESS.value

    @unittest.skip("reconfigure_vapp_network is not a valid method")
    def test_011_update_vapp_network(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        vapp = vdc.get_vapp(self.config['vcd']['vapp'])
        assert self.config['vcd']['vapp'] == vapp.get('name')
        result = vdc.reconfigure_vapp_network(self.config['vcd']['vapp'],
                                              'net2',
                                              self.config['vcd']['fence_mode'])
        task = self.client.get_task_monitor().wait_for_status(
            task=result,
            timeout=60,
            poll_frequency=2,
            fail_on_statuses=None,
            expected_target_statuses=[
                TaskStatus.SUCCESS, TaskStatus.ABORTED, TaskStatus.ERROR,
                TaskStatus.CANCELED
            ],
            callback=None)
        assert task.get('status') == TaskStatus.SUCCESS.value

    def test_012_add_disk(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        assert self.config['vcd']['vapp'] == vapp_resource.get('name')
        vm_name = self.config['vcd']['vm']
        vapp = VApp(self.client, resource=vapp_resource)
        disk_size = 1024  # 1GB
        result = vapp.add_disk_to_vm(vm_name, disk_size)
        task = self.client.get_task_monitor().wait_for_status(
            task=result,
            timeout=60,
            poll_frequency=2,
            fail_on_statuses=None,
            expected_target_statuses=[
                TaskStatus.SUCCESS, TaskStatus.ABORTED, TaskStatus.ERROR,
                TaskStatus.CANCELED
            ],
            callback=None)
        assert task.get('status') == TaskStatus.SUCCESS.value

    @unittest.skip("param identical is invalid")
    def test_100_instantiate_vapp_identical(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        result = vdc.instantiate_vapp(
            self.config['vcd']['vapp'],
            self.config['vcd']['catalog'],
            self.config['vcd']['template'],
            network=self.config['vcd']['network'],
            fence_mode='bridged',
            deploy=True,
            power_on=False,
            identical=True)
        task = self.client.get_task_monitor().wait_for_status(
            task=result.Tasks.Task[0],
            timeout=60,
            poll_frequency=2,
            fail_on_statuses=None,
            expected_target_statuses=[
                TaskStatus.SUCCESS, TaskStatus.ABORTED, TaskStatus.ERROR,
                TaskStatus.CANCELED
            ],
            callback=None)
        assert task.get('status') == TaskStatus.SUCCESS.value
        vdc.reload()
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        vm = vapp_resource.xpath(
            '//vcloud:VApp/vcloud:Children/vcloud:Vm', namespaces=NSMAP)
        assert len(vm) > 0
        assert vm[0].get('name') == self.config['vcd']['vm']

    def test_101_connect_orgvdc_network(self):
        org_in_use = self.config['vcd']['org_in_use']
        org = Org(self.client,
                  href=self.client.get_org_by_name(org_in_use).get('href'))
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        vapp = VApp(self.client, resource=vapp_resource)
        result = vapp.connect_org_vdc_network(self.config['vcd'][
                                                 'orgvdc_network'])
        task = self.client.get_task_monitor().wait_for_status(
            task=result,
            timeout=60,
            poll_frequency=2,
            fail_on_statuses=None,
            expected_target_statuses=[
                TaskStatus.SUCCESS, TaskStatus.ABORTED, TaskStatus.ERROR,
                TaskStatus.CANCELED
            ],
            callback=None)
        assert task.get('status') == TaskStatus.SUCCESS.value

    def test_102_disconnect_orgvdc_network(self):
        org_in_use = self.config['vcd']['org_in_use']
        org = Org(self.client,
                  href=self.client.get_org_by_name(org_in_use).get('href'))
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        vapp = VApp(self.client, resource=vapp_resource)
        result = vapp.disconnect_org_vdc_network(self.config['vcd'][
                                                 'orgvdc_network'])
        task = self.client.get_task_monitor().wait_for_status(
            task=result,
            timeout=60,
            poll_frequency=2,
            fail_on_statuses=None,
            expected_target_statuses=[
                TaskStatus.SUCCESS, TaskStatus.ABORTED, TaskStatus.ERROR,
                TaskStatus.CANCELED
            ],
            callback=None)
        assert task.get('status') == TaskStatus.SUCCESS.value

    def test_11_change_owner(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        user_resource = org.get_user(self.config['vcd']['new_vapp_user'])
        vdc = VDC(self.client, href=vdc_resource.get('href'))
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        vapp = VApp(self.client, resource=vapp_resource)
        vapp.change_owner(user_resource.get('href'))

        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        assert self.config['vcd']['new_vapp_user'] == \
            vapp_resource.Owner.User.get('name')

    def test_110_instantiate_vapp_custom_disk_size(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        result = vdc.instantiate_vapp(
            self.config['vcd']['vapp'],
            self.config['vcd']['catalog'],
            self.config['vcd']['template'],
            network=self.config['vcd']['network'],
            fence_mode='bridged',
            deploy=True,
            power_on=False,
            disk_size=self.config['vcd']['disk_size_new'])
        task = self.client.get_task_monitor().wait_for_status(
            task=result.Tasks.Task[0],
            timeout=60,
            poll_frequency=2,
            fail_on_statuses=None,
            expected_target_statuses=[
                TaskStatus.SUCCESS, TaskStatus.ABORTED, TaskStatus.ERROR,
                TaskStatus.CANCELED
            ],
            callback=None)
        assert task.get('status') == TaskStatus.SUCCESS.value
        vdc.resource = vdc.client.get_resource(vdc.href)
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        vms = vapp_resource.xpath(
            '//vcloud:VApp/vcloud:Children/vcloud:Vm', namespaces=NSMAP)
        assert len(vms) > 0

        items = vms[0].xpath(
            '//ovf:VirtualHardwareSection/ovf:Item',
            namespaces={
                'ovf': NSMAP['ovf']
            })
        assert len(items) > 0

        found_disk = False
        for item in items:
            if item['{' + NSMAP['rasd'] + '}ResourceType'] == 17:  # NOQA
                found_disk = True
                assert item['{' + NSMAP['rasd'] + '}VirtualQuantity'] == \
                    (self.config['vcd']['disk_size_new'] * 1024 * 1024)
                break

        # this check makes sure that the vm isn't disk-less
        assert found_disk

        # cleanup
        self.test_100_delete_vapp()

    def test_1000_delete_vapp(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        result = vdc.delete_vapp(self.config['vcd']['vapp'], force=True)
        task = self.client.get_task_monitor().wait_for_status(
            task=result,
            timeout=60,
            poll_frequency=2,
            fail_on_statuses=None,
            expected_target_statuses=[
                TaskStatus.SUCCESS, TaskStatus.ABORTED, TaskStatus.ERROR,
                TaskStatus.CANCELED
            ],
            callback=None)
        assert task.get('status') == TaskStatus.SUCCESS.value

    def test_1001_remove_all_vapp_access(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=vdc_resource)
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        vapp = VApp(self.client, resource=vapp_resource)
        control_access = vapp.remove_access_settings(remove_all=True)
        self.assertFalse(hasattr(control_access, 'AccessSettings'))

    def test_1002_add_vapp_access(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=vdc_resource)
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        vapp = VApp(self.client, resource=vapp_resource)
        control_access = vapp.add_access_settings(
            access_settings_list=[
                {'name': self.config['vcd']['access_user'], 'type': 'user'},
                {'name': self.config['vcd']['access_user1'], 'type': 'user',
                 'access_level': 'Change'}
            ])
        assert len(control_access.AccessSettings.AccessSetting) == 2

    def test_1003_get_vapp_access(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=vdc_resource)
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        vapp = VApp(self.client, resource=vapp_resource)
        control_access = vapp.get_access_settings()
        assert len(control_access.AccessSettings.AccessSetting) == 2

    def test_1004_remove_vapp_access(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=vdc_resource)
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        vapp = VApp(self.client, resource=vapp_resource)
        control_access = vapp.remove_access_settings(
            access_settings_list=[
                {'name': self.config['vcd']['access_user'], 'type': 'user'}
            ])
        assert len(control_access.AccessSettings.AccessSetting) == 1

    def test_1005_share_vapp_access(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=vdc_resource)
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        vapp = VApp(self.client, resource=vapp_resource)
        control_access = vapp.share_with_org_members(
            everyone_access_level='ReadOnly')
        assert control_access.IsSharedToEveryone.text == 'true'
        assert control_access.EveryoneAccessLevel.text == 'ReadOnly'

    def test_1006_unshare_vapp_access(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=vdc_resource)
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        vapp = VApp(self.client, resource=vapp_resource)
        control_access = vapp.unshare_from_org_members()
        assert control_access.IsSharedToEveryone.text == 'false'


if __name__ == '__main__':
    unittest.main()
