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

import os
import unittest
import yaml
from pyvcloud.vcd.client import BasicLoginCredentials
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import TaskStatus
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.test import TestCase
from pyvcloud.vcd.vdc import VDC
from pyvcloud.vcd.vapp import VApp


class TestVAppVM(TestCase):

    def test_0001_create_vapp(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        result = vdc.create_vapp(self.config['vcd']['vapp'],
                                 network=self.config['vcd']['network'],
                                 fence_mode=self.config['vcd']['fence_mode'])
        task = self.client.get_task_monitor().wait_for_status(
                            task=result.Tasks.Task[0],
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

    def test_0002_add_vm(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=vdc_resource.get('href'))
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        assert vapp_resource.get('name') == self.config['vcd']['vapp']
        vapp = VApp(self.client, resource=vapp_resource)
        catalog_item = org.get_catalog_item(self.config['vcd']['catalog'],
                                            self.config['vcd']['template'])
        source_vapp_resource = self.client.get_resource(
            catalog_item.Entity.get('href'))
        spec = {'source_vm_name': self.config['vcd']['vm'],
                'vapp': source_vapp_resource}
        spec['target_vm_name'] = self.config['vcd']['hostname']
        spec['hostname'] = self.config['vcd']['hostname']
        spec['network'] = self.config['vcd']['network']
        spec['ip_allocation_mode'] = self.config['vcd']['ip_allocation_mode']
        spec['storage_profile'] = vdc.get_storage_profile(
            self.config['vcd']['storage_profile'])
        vms = [spec]
        result = vapp.add_vms(vms)
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
                                TaskStatus.SUCCESS,
                                TaskStatus.ABORTED,
                                TaskStatus.ERROR,
                                TaskStatus.CANCELED],
                            callback=None)
        assert task.get('status') == TaskStatus.SUCCESS.value

    def test_1002_deploy_vapp(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        assert vapp_resource.get('name') == self.config['vcd']['vapp']
        vapp = VApp(self.client, resource=vapp_resource)
        result = vapp.deploy()
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

    def test_1003_reset_vapp(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        assert vapp_resource.get('name') == self.config['vcd']['vapp']
        vapp = VApp(self.client, resource=vapp_resource)
        result = vapp.power_reset()
        # result = vapp.reboot()
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

    def test_1004_shutdown_vapp(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        assert vapp_resource.get('name') == self.config['vcd']['vapp']
        vapp = VApp(self.client, resource=vapp_resource)
        result = vapp.shutdown()
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

    def test_1005_reboot_vapp(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        assert vapp_resource.get('name') == self.config['vcd']['vapp']
        vapp = VApp(self.client, resource=vapp_resource)
        result = vapp.reboot()
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

if __name__ == '__main__':
    unittest.main()
