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

class TestVAppVM(TestCase):

    def test_0001_modify_cpu(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))
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
                            fail_on_status=None,
                            expected_target_statuses=[
                                TaskStatus.SUCCESS,
                                TaskStatus.ABORTED,
                                TaskStatus.ERROR,
                                TaskStatus.CANCELED],
                            callback=None)
        assert task.get('status') == TaskStatus.SUCCESS.value

    def test_0002_modify_memory(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))
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
                            fail_on_status=None,
                            expected_target_statuses=[
                                TaskStatus.SUCCESS,
                                TaskStatus.ABORTED,
                                TaskStatus.ERROR,
                                TaskStatus.CANCELED],
                            callback=None)
        assert task.get('status') == TaskStatus.SUCCESS.value

    def test_0003_power_on(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))
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
                            fail_on_status=None,
                            expected_target_statuses=[
                                TaskStatus.SUCCESS,
                                TaskStatus.ABORTED,
                                TaskStatus.ERROR,
                                TaskStatus.CANCELED],
                            callback=None)
        assert task.get('status') == TaskStatus.SUCCESS.value

if __name__ == '__main__':
    unittest.main()
