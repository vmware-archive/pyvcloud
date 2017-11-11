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

class TestVApp(TestCase):

    def test_010_instantiate_vapp(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        result = vdc.instantiate_vapp(self.config['vcd']['vapp'],
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
                            fail_on_status=None,
                            expected_target_statuses=[
                                TaskStatus.SUCCESS,
                                TaskStatus.ABORTED,
                                TaskStatus.ERROR,
                                TaskStatus.CANCELED],
                            callback=None)
        assert task.get('status') == TaskStatus.SUCCESS.value

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
                            fail_on_status=None,
                            expected_target_statuses=[
                                TaskStatus.SUCCESS,
                                TaskStatus.ABORTED,
                                TaskStatus.ERROR,
                                TaskStatus.CANCELED],
                            callback=None)
        assert task.get('status') == TaskStatus.SUCCESS.value

    def test_100_delete_vapp(self):
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
                            fail_on_status=None,
                            expected_target_statuses=[
                                TaskStatus.SUCCESS,
                                TaskStatus.ABORTED,
                                TaskStatus.ERROR,
                                TaskStatus.CANCELED],
                            callback=None)
        assert task.get('status') == TaskStatus.SUCCESS.value

    def test_110_instantiate_vapp_identical(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        result = vdc.instantiate_vapp(self.config['vcd']['vapp'],
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
                            fail_on_status=None,
                            expected_target_statuses=[
                                TaskStatus.SUCCESS,
                                TaskStatus.ABORTED,
                                TaskStatus.ERROR,
                                TaskStatus.CANCELED],
                            callback=None)
        assert task.get('status') == TaskStatus.SUCCESS.value
        # vdc.reload()
        vdc.resource = vdc.client.get_resource(vdc.href)
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        vm = vapp_resource.xpath(
            '//vcloud:VApp/vcloud:Children/vcloud:Vm',
            namespaces=NSMAP)
        assert len(vm) > 0
        assert vm[0].get('name') == self.config['vcd']['vm']

    def test_111_instantiate_vapp_custom_disk_size(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        result = vdc.instantiate_vapp(self.config['vcd']['vapp'],
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
                            fail_on_status=None,
                            expected_target_statuses=[
                                TaskStatus.SUCCESS,
                                TaskStatus.ABORTED,
                                TaskStatus.ERROR,
                                TaskStatus.CANCELED],
                            callback=None)
        assert task.get('status') == TaskStatus.SUCCESS.value
        vdc.resource = vdc.client.get_resource(vdc.href)
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        vms = vapp_resource.xpath(
            '//vcloud:VApp/vcloud:Children/vcloud:Vm',
            namespaces=NSMAP)
        assert len(vms) > 0

        items = vms[0].xpath('//ovf:VirtualHardwareSection/ovf:Item',
            namespaces={'ovf': NSMAP['ovf']})
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

if __name__ == '__main__':
    unittest.main()
