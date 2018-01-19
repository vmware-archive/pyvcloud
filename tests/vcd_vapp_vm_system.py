# VMware vCloud Director Python SDK
# Copyright (c) 2018 VMware, Inc. All Rights Reserved.
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


class TestVAppVMSystem(TestCase):

    def test_0001_create_vapp(self):
        org_resource = self.client.get_org_by_name(
            self.config['vcd']['org_to_use'])
        self.logger.debug('org: %s' % org_resource.get('name'))
        org = Org(self.client, href=org_resource.get('href'))
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=vdc_resource)
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        result = vdc.create_vapp(self.config['vcd']['vapp'],
                                 network=self.config['vcd']['network'],
                                 fence_mode=self.config['vcd']['fence_mode'])
        task = self.client.get_task_monitor().wait_for_status(
                            task=result.Tasks.Task[0])
        assert task.get('status') == TaskStatus.SUCCESS.value

    def test_0002_add_vm(self):
        org_resource = self.client.get_org_by_name(
            self.config['vcd']['org_to_use'])
        self.logger.debug('org: %s' % org_resource.get('name'))
        org = Org(self.client, href=org_resource.get('href'))
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
        result = vapp.add_vms(vms, all_eulas_accepted=True)
        task = self.client.get_task_monitor().wait_for_status(task=result)
        assert task.get('status') == TaskStatus.SUCCESS.value

    def test_0003_get_vm_info(self):
        org_resource = self.client.get_org_by_name(
            self.config['vcd']['org_to_use'])
        self.logger.debug('org: %s' % org_resource.get('name'))
        org = Org(self.client, href=org_resource.get('href'))
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=vdc_resource)
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        vapp_resource = vdc.get_vapp(self.config['vcd']['vapp'])
        assert self.config['vcd']['vapp'] == vapp_resource.get('name')
        vapp = VApp(self.client, resource=vapp_resource)
        vm_name = self.config['vcd']['hostname']
        vm_resource = vapp.get_vm(vm_name)
        self.logger.debug('vm name: %s' % vm_resource.get('name'))
        vm = VM(self.client, resource=vm_resource)
        vcenter = vm.get_vc()
        self.logger.debug('vCenter: %s' % vcenter)
        assert vcenter == self.config['vcd']['vcenter']

    def test_1000_delete_vapp(self):
        org_resource = self.client.get_org_by_name(
            self.config['vcd']['org_to_use'])
        self.logger.debug('org: %s' % org_resource.get('name'))
        org = Org(self.client, href=org_resource.get('href'))
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=vdc_resource)
        assert self.config['vcd']['vdc'] == vdc.get_resource().get('name')
        result = vdc.delete_vapp(self.config['vcd']['vapp'], force=True)
        task = self.client.get_task_monitor().wait_for_status(task=result)
        assert task.get('status') == TaskStatus.SUCCESS.value

if __name__ == '__main__':
    unittest.main()
