import os
import unittest
import yaml
from pyvcloud.vcd.client import BasicLoginCredentials
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.vdc import VDC
from pyvcloud.vcd.test import TestCase
from lxml import etree
from pyvcloud.vcd.client import TaskStatus

class TestDiskTeardown(TestCase):


    def test_008_delete_all_disks(self):

        logged_in_org = self.client.get_org()
       
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))
        
        disks = vdc.get_disks()
        
        for disk in disks:
             print ("Deleting disk: " + disk.get('id'))
             taskObj = vdc.delete_disk(None, disk.get('id'))
             print ("Deleted VDC disk: " + str(etree.tostring(taskObj, pretty_print=True), "utf-8"))
             
             #print("VDC Disk: " + str(disk))

             task = self.client.get_task_monitor().wait_for_status(
                        task=taskObj,
                        timeout=30,
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