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
from pyvcloud.vcd.vapp import VApp
from pyvcloud.vcd.vdc import VDC
from pyvcloud.vcd.vm import VM

class TestVM(TestCase):

    def test_0001_modify_cpu(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=vdc_resource)
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        vapp = VApp(self.client, resource=vapp_resource)
        vm_resource = vapp.get_vm(self.config['vcd']['vm'])
        vm = VM(self.client, resource=vm_resource)
        task = vm.modify_cpu(self.config['vcd']['cpu'],
                             self.config['vcd']['cores_per_socket'])
        task = self.client.get_task_monitor().wait_for_status(
                            task=task,
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
        vm.reload()
        cpus = vm.get_cpus()
        assert cpus['num_cpus'] == self.config['vcd']['cpu']
        assert cpus['num_cores_per_socket'] == self.config['vcd']['cores_per_socket']

    def test_0002_modify_memory(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=vdc_resource)
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        vapp = VApp(self.client, resource=vapp_resource)
        vm_resource = vapp.get_vm(self.config['vcd']['vm'])
        vm = VM(self.client, resource=vm_resource)
        task = vm.modify_memory(self.config['vcd']['memory'])
        task = self.client.get_task_monitor().wait_for_status(
                            task=task,
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
        vm.reload()
        assert vm.get_memory() == self.config['vcd']['memory']

    def test_0003_power_on(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=vdc_resource)
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        vapp = VApp(self.client, resource=vapp_resource)
        vm_resource = vapp.get_vm(self.config['vcd']['vm'])
        vm = VM(self.client, resource=vm_resource)
        task = vm.power_on()
        task = self.client.get_task_monitor().wait_for_status(
                            task=task,
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

    def test_0004_power_reset(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=vdc_resource)
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        vapp = VApp(self.client, resource=vapp_resource)
        vm_resource = vapp.get_vm(self.config['vcd']['vm'])
        vm = VM(self.client, resource=vm_resource)
        task = vm.power_reset()
        task = self.client.get_task_monitor().wait_for_status(
                            task=task,
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

    def test_0005_power_off(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=vdc_resource)
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        vapp = VApp(self.client, resource=vapp_resource)
        vm_resource = vapp.get_vm(self.config['vcd']['vm'])
        vm = VM(self.client, resource=vm_resource)
        task = vm.power_off()
        task = self.client.get_task_monitor().wait_for_status(
            task=task,
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

    def test_0006_undeploy(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=vdc_resource)
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        vapp = VApp(self.client, resource=vapp_resource)
        vm_resource = vapp.get_vm(self.config['vcd']['vm'])
        vm = VM(self.client, resource=vm_resource)
        task = vm.undeploy()
        task = self.client.get_task_monitor().wait_for_status(task)
        assert task.get('status') == TaskStatus.SUCCESS.value

    def test_0007_delete(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=vdc_resource)
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        vapp = VApp(self.client, resource=vapp_resource)
        task = vapp.delete_vms([self.config['vcd']['vm']])
        task = self.client.get_task_monitor().wait_for_status(task)
        assert task.get('status') == TaskStatus.SUCCESS.value

    def test_1002_deploy_vm(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        assert vapp_resource.get('name') == self.config['vcd']['vapp']
        vapp = VApp(self.client, resource=vapp_resource)
        vm_resource = vapp.get_vm(self.config['vcd']['vm'])
        vm = VM(self.client, resource=vm_resource)
        result = vm.deploy()
        # result = vm.shutdown()
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

    def test_0008_shutdown_vm(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        assert vapp_resource.get('name') == self.config['vcd']['vapp']
        vapp = VApp(self.client, resource=vapp_resource)
        vm_resource = vapp.get_vm(self.config['vcd']['vm'])
        vm = VM(self.client, resource=vm_resource)
        result = vm.shutdown()
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

    def test_0009_reboot_vm(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        assert vapp_resource.get('name') == self.config['vcd']['vapp']
        vapp = VApp(self.client, resource=vapp_resource)
        vm_resource = vapp.get_vm(self.config['vcd']['vm'])
        vm = VM(self.client, resource=vm_resource)
        result = vm.reboot()
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

    def test_1004_shutdown_vm(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        assert vapp_resource.get('name') == self.config['vcd']['vapp']
        vapp = VApp(self.client, resource=vapp_resource)
        vm_resource = vapp.get_vm(self.config['vcd']['vm'])
        vm = VM(self.client, resource=vm_resource)
        result = vm.shutdown()
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

    def test_1005_reboot_vm(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        assert vapp_resource.get('name') == self.config['vcd']['vapp']
        vapp = VApp(self.client, resource=vapp_resource)
        vm_resource = vapp.get_vm(self.config['vcd']['vm'])
        vm = VM(self.client, resource=vm_resource)
        result = vm.reboot()
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

    def test_1006_snapshot_create(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=vdc_resource)
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        assert vapp_resource.get('name') == self.config['vcd']['vapp']
        vapp = VApp(self.client, resource=vapp_resource)
        vm_resource = vapp.get_vm(self.config['vcd']['vm'])
        assert vm_resource.get('name') == self.config['vcd']['vm']
        vm = VM(self.client, resource=vm_resource)
        task = vm.snapshot_create(memory=False, quiesce=False)
        task = self.client.get_task_monitor().wait_for_status(
                            task=task,
                            timeout=120,
                            poll_frequency=2,
                            fail_on_statuses=None,
                            expected_target_statuses=[
                                TaskStatus.SUCCESS,
                                TaskStatus.ABORTED,
                                TaskStatus.ERROR,
                                TaskStatus.CANCELED],
                            callback=None)
        assert task.get('status') == TaskStatus.SUCCESS.value

    def test_1007_snapshot_revert_to_current(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=vdc_resource)
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        vapp = VApp(self.client, resource=vapp_resource)
        vm_resource = vapp.get_vm(self.config['vcd']['vm'])
        vm = VM(self.client, resource=vm_resource)
        task = vm.snapshot_revert_to_current()
        task = self.client.get_task_monitor().wait_for_status(
            task=task,
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

    def test_1008_snapshot_remove_all(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=vdc_resource)
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        vapp = VApp(self.client, resource=vapp_resource)
        vm_resource = vapp.get_vm(self.config['vcd']['vm'])
        vm = VM(self.client, resource=vm_resource)
        task = vm.snapshot_remove_all()
        task = self.client.get_task_monitor().wait_for_status(
            task=task,
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
