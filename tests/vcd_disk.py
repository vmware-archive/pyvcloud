import os
import unittest
import yaml
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.test import TestCase
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.vdc import VDC
from lxml import etree
from pyvcloud.vcd.utils import stdout_xml
from pyvcloud.vcd.client import TaskStatus


class TestDisk(TestCase):
    
    """
    def test_008_get_disks(self):

        logged_in_org = self.client.get_org()
       
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        
        disks = vdc.get_disks()
        assert len(disks) > 0  
        assert disks[0].get('name') == self.config['vcd']['disk']
        for disk in disks:
             print ("VDC disk: " + str(etree.tostring(disk, pretty_print=True), "utf-8"))
    """

    def test_008_get_disks(self):

        logged_in_org = self.client.get_org()
       
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))
        
        disks = vdc.get_disks()
        
        for disk in disks:
            print (" Disk: " + str(etree.tostring(disk, pretty_print=True), "utf-8"))

        assert len(disks) > 0 

        assert disks[0].get('name') == self.config['vcd']['disk']



    def test_008_get_disk(self):

        logged_in_org = self.client.get_org()
       
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))

        
        fetched_disk = vdc.get_disk("Disk1")
        
        assert fetched_disk is not None  


    def test_008_update_disk(self):

        logged_in_org = self.client.get_org()
       
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))

        
        taskObj = vdc.update_disk(self.config['vcd']['disk'], "3072", "DiskUpdated", "3 GB Disk")
        
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

        print ("Updating VDC disk: " + str(etree.tostring(task, pretty_print=True), "utf-8"))

    def test_008_update_disk_iops(self):
        logged_in_org = self.client.get_org()

        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))

        taskObj = vdc.update_disk(self.config['vcd']['disk'], "3072", "DiskUpdated",
                                  "3 GB Disk",
                                  "stf-storage-service-gold",
                                  "200")

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

        print ("Updating VDC disk: " + str(etree.tostring(task, pretty_print=True), "utf-8"))

    def test_008_update_disk_storage_profile(self):
        logged_in_org = self.client.get_org()

        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))

        taskObj = vdc.update_disk(self.config['vcd']['disk'], "3072", "DiskUpdated", "3 GB Disk", "*", "200")

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

        print ("Updating VDC disk: " + str(etree.tostring(task, pretty_print=True), "utf-8"))

    def test_008_get_disk_by_id(self):

        logged_in_org = self.client.get_org()
       
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))
        
        disks = vdc.get_disks()
        assert len(disks) > 0  

        # get first disk using id
        fetched_disk = vdc.get_disk(None, disks[0].get('id'))
        assert fetched_disk is not None  


    
    def test_010_get_storage_profiles(self):

        logged_in_org = self.client.get_org()
       
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))

        profiles = vdc.get_storage_profiles()
        assert len(profiles) > 0
        assert profiles[0].get('name')== self.config['vcd']['storage_profile']
        
    def test_010_get_storage_profile(self):

        logged_in_org = self.client.get_org()
       
        org = Org(self.client, resource=logged_in_org)
        v = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, href=v.get('href'))

        profile = vdc.get_storage_profile(self.config['vcd']['storage_profile'])
        print("Storage Profile: " + str(profile))
        assert profile.get('name') == self.config['vcd']['storage_profile']

    def test_111_change_owner_disk(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        user_resource = org.get_user(self.config['vcd']['new_disk_user'])
        vdc = VDC(self.client, href=vdc_resource.get('href'))
        disk = vdc.change_disk_owner(self.config['vcd']['disk'],
                                     user_resource.get('href'), self.config['vcd']['disk_id'])
        disk_resource = vdc.get_disk(self.config['vcd']['disk'])
        new_user = disk_resource.Owner.User.get('name')
        assert self.config['vcd']['new_disk_user'] == disk_resource.Owner.User.get('name')

if __name__ == '__main__':
    unittest.main()
