# VMware vCloud Director Python SDK
# Copyright (c) 2017 VMware, Inc. All Rights Reserved.
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

from pyvcloud.vcd.client import TaskStatus
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.test import TestCase
from pyvcloud.vcd.vdc import VDC
import unittest


class TestVDC(TestCase):
    def test_list_vdc(self):
        org_resource = self.client.get_org()
        org = Org(self.client, resource=org_resource)
        vdcs = org.list_vdcs()
        assert vdcs is not None

    def test_list_org_vdc(self):
        org_to_use = self.client.get_org_by_name(
            self.config['vcd']['org_to_use'])
        org = Org(self.client, href=org_to_use.get('href'))
        assert org is not None
        vdcs = org.list_vdcs()
        assert len(vdcs) > 0

    def test_create_vdc(self):
        org_to_use = self.client.get_org_by_name(
            self.config['vcd']['org_to_use'])
        org = Org(self.client, href=org_to_use.get('href'))
        storage_profiles = [{
            'name': self.config['vcd']['storage_profile'],
            'enabled': True,
            'units': 'MB',
            'limit': 0,
            'default': True
        }]
        vdc_resource = org.create_org_vdc(
            self.config['vcd']['new_vdc'],
            self.config['vcd']['provider_vdc'],
            network_pool_name=self.config['vcd']['network_pool'],
            description='description',
            allocation_model='AllocationVApp',
            cpu_allocated=0,
            cpu_limit=0,
            storage_profiles=storage_profiles,
            uses_fast_provisioning=True,
            is_thin_provision=True)
        task = self.client.get_task_monitor().wait_for_status(
            task=vdc_resource.Tasks.Task[0],
            timeout=30,
            poll_frequency=2,
            fail_on_status=None,
            expected_target_statuses=[
                TaskStatus.SUCCESS, TaskStatus.ABORTED, TaskStatus.ERROR,
                TaskStatus.CANCELED
            ],
            callback=None)
        assert task.get('status') == TaskStatus.SUCCESS.value

    def test_get_vdc(self):
        org_to_use = self.client.get_org_by_name(
            self.config['vcd']['org_to_use'])
        org = Org(self.client, href=org_to_use.get('href'))
        resource = org.get_vdc(self.config['vcd']['new_vdc'])
        assert resource is not None
        vdc = VDC(self.client, resource=resource)
        assert self.config['vcd']['new_vdc'] == vdc.get_resource().get('name')

    def test_disable_vdc(self):
        org_to_use = self.client.get_org_by_name(
            self.config['vcd']['org_to_use'])
        org = Org(self.client, href=org_to_use.get('href'))
        resource = org.get_vdc(self.config['vcd']['new_vdc'])
        vdc = VDC(self.client, resource=resource)
        vdc.enable_vdc(False)
        vdc.reload()
        assert vdc.resource.IsEnabled.text == 'false'

    def test_delete_vdc(self):
        org_to_use = self.client.get_org_by_name(
            self.config['vcd']['org_to_use'])
        org = Org(self.client, href=org_to_use.get('href'))
        t = org.delete_org_vdc(self.config['vcd']['new_vdc'])
        task = self.client.get_task_monitor().wait_for_status(
            task=t,
            timeout=30,
            poll_frequency=2,
            fail_on_status=None,
            expected_target_statuses=[
                TaskStatus.SUCCESS, TaskStatus.ABORTED, TaskStatus.ERROR,
                TaskStatus.CANCELED
            ],
            callback=None)
        assert task.get('status') == TaskStatus.SUCCESS.value

    def test_vdc_control_access_retrieval(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=vdc_resource)
        access_control_settings = vdc.get_access_control_settings()
        assert len(access_control_settings) > 0


if __name__ == '__main__':
    unittest.main()
