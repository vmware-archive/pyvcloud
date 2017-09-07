import os
import unittest
import yaml
from pyvcloud.vcd.client import BasicLoginCredentials
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.client import TaskStatus
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.test import TestCase
from pyvcloud.vcd.vdc import VDC

class TestVApp(TestCase):

    def test_010_instantiate_vapp(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, org_resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, vdc_href=v.get('href'))
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
        org = Org(self.client, org_resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, vdc_href=v.get('href'))
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
        org = Org(self.client, org_resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, vdc_href=v.get('href'))
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


if __name__ == '__main__':
    unittest.main()
