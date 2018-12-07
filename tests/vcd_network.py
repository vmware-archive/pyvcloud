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

from pyvcloud.vcd.client import TaskStatus
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.platform import Platform
from pyvcloud.vcd.test import TestCase
from pyvcloud.vcd.vdc import VDC


class TestNetwork(TestCase):

    def test_005_create_routed_orgvdc_network(self):
        org_record = self.client.get_org_by_name(
            self.config['vcd']['org_name'])
        org = Org(self.client, href=org_record.get('href'))
        vdc_resource = org.get_vdc(self.config['vcd']['vdc_name'])
        vdc = VDC(self.client, href=vdc_resource.get('href'))

        result = vdc.create_routed_vdc_network(
            network_name=self.config['vcd']['vdc_routed_network_name'],
            gateway_name=self.config['vcd']['routed_network_gateway_name'],
            network_cidr=self.config['vcd']['network_cidr'],
            description='Dummy description')
        task = self.client.get_task_monitor().wait_for_success(
            task=result.Tasks.Task[0])
        assert task.get('status') == TaskStatus.SUCCESS.value

    def test_010_create_direct_orgvdc_network(self):
        org_record = self.client.get_org_by_name(
            self.config['vcd']['org_name'])
        org = Org(self.client, href=org_record.get('href'))
        vdc_resource = org.get_vdc(self.config['vcd']['vdc_name'])
        vdc = VDC(self.client, href=vdc_resource.get('href'))

        result = vdc.create_directly_connected_vdc_network(
            network_name=self.config['vcd']['vdc_direct_network_name'],
            parent_network_name=self.config['vcd']['ext_network_name'],
            description='Dummy description')
        task = self.client.get_task_monitor().wait_for_success(
            task=result.Tasks.Task[0])
        assert task.get('status') == TaskStatus.SUCCESS.value

    def test_020_create_isolated_orgvdc_network(self):
        org_record = self.client.get_org_by_name(
            self.config['vcd']['org_name'])
        org = Org(self.client, href=org_record.get('href'))
        vdc_resource = org.get_vdc(self.config['vcd']['vdc_name'])
        vdc = VDC(self.client, href=vdc_resource.get('href'))

        result = vdc.create_isolated_vdc_network(
            network_name=self.config['vcd']['vdc_isolated_network_name'],
            gateway_ip=self.config['vcd']['isolated_network_gateway_ip'],
            netmask=self.config['vcd']['isolated_network_gateway_netmask'],
            description='Dummy description')
        task = self.client.get_task_monitor().wait_for_success(
            task=result.Tasks.Task[0])
        assert task.get('status') == TaskStatus.SUCCESS.value

    def test_030_list_external_networks(self):
        platform = Platform(self.client)
        ext_net_refs = platform.list_external_networks()
        assert len(ext_net_refs) > 0

    def test_035_list_routed_orgvdc_networks(self):
        org_record = self.client.get_org_by_name(
            self.config['vcd']['org_name'])
        org = Org(self.client, href=org_record.get('href'))
        vdc_resource = org.get_vdc(self.config['vcd']['vdc_name'])
        vdc = VDC(self.client, href=vdc_resource.get('href'))

        result = vdc.list_orgvdc_routed_networks()
        assert len(result) > 0

    def test_040_list_direct_orgvdc_networks(self):
        org_record = self.client.get_org_by_name(
            self.config['vcd']['org_name'])
        org = Org(self.client, href=org_record.get('href'))
        vdc_resource = org.get_vdc(self.config['vcd']['vdc_name'])
        vdc = VDC(self.client, href=vdc_resource.get('href'))

        result = vdc.list_orgvdc_direct_networks()
        assert len(result) > 0

    def test_050_list_isolated_orgvdc_networks(self):
        org_record = self.client.get_org_by_name(
            self.config['vcd']['org_name'])
        org = Org(self.client, href=org_record.get('href'))
        vdc_resource = org.get_vdc(self.config['vcd']['vdc_name'])
        vdc = VDC(self.client, href=vdc_resource.get('href'))

        result = vdc.list_orgvdc_isolated_networks()
        assert len(result) > 0

    def test_180_delete_routed_orgvdc_networks(self):
        org_record = self.client.get_org_by_name(
            self.config['vcd']['org_name'])
        org = Org(self.client, href=org_record.get('href'))
        vdc_resource = org.get_vdc(self.config['vcd']['vdc_name'])
        vdc = VDC(self.client, href=vdc_resource.get('href'))

        result = vdc.delete_routed_orgvdc_network(
            name=self.config['vcd']['vdc_routed_network_name'], force=True)
        task = self.client.get_task_monitor().wait_for_success(
            task=result)
        assert task.get('status') == TaskStatus.SUCCESS.value

    def test_190_delete_direct_orgvdc_networks(self):
        org_record = self.client.get_org_by_name(
            self.config['vcd']['org_name'])
        org = Org(self.client, href=org_record.get('href'))
        vdc_resource = org.get_vdc(self.config['vcd']['vdc_name'])
        vdc = VDC(self.client, href=vdc_resource.get('href'))

        result = vdc.delete_direct_orgvdc_network(
            name=self.config['vcd']['vdc_direct_network_name'], force=True)
        task = self.client.get_task_monitor().wait_for_success(
            task=result)
        assert task.get('status') == TaskStatus.SUCCESS.value

    def test_200_delete_isolated_orgvdc_networks(self):
        org_record = self.client.get_org_by_name(
            self.config['vcd']['org_name'])
        org = Org(self.client, href=org_record.get('href'))
        vdc_resource = org.get_vdc(self.config['vcd']['vdc_name'])
        vdc = VDC(self.client, href=vdc_resource.get('href'))

        result = vdc.delete_isolated_orgvdc_network(
            name=self.config['vcd']['vdc_isolated_network_name'], force=True)
        task = self.client.get_task_monitor().wait_for_success(
            task=result)
        assert task.get('status') == TaskStatus.SUCCESS.value


if __name__ == '__main__':
    unittest.main()
