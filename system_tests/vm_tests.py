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

import unittest
from uuid import uuid1

from pyvcloud.system_test_framework.base_test import BaseTestCase
from pyvcloud.system_test_framework.environment import CommonRoles
from pyvcloud.system_test_framework.environment import developerModeAware
from pyvcloud.system_test_framework.environment import Environment
from pyvcloud.system_test_framework.utils import \
    create_customized_vapp_from_template
from pyvcloud.system_test_framework.utils import create_empty_vapp

from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import IpAddressMode
from pyvcloud.vcd.client import NetworkAdapterType
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.client import TaskStatus
from pyvcloud.vcd.client import VmNicProperties
from pyvcloud.vcd.exceptions import EntityNotFoundException
from pyvcloud.vcd.vapp import VApp
from pyvcloud.vcd.vm import VM


class TestVM(BaseTestCase):
    """Test vm functionalities implemented in pyvcloud."""

    _test_runner_role = CommonRoles.VAPP_AUTHOR
    _client = None

    _test_vapp_name = 'test_vApp_' + str(uuid1())
    _test_vapp_first_vm_num_cpu = 2
    _test_vapp_first_vm_new_num_cpu = 4
    _test_vapp_first_vm_memory_size = 64  # MB
    _test_vapp_first_vm_new_memory_size = 128  # MB
    _test_vapp_first_vm_first_disk_size = 100  # MB
    _test_vapp_first_vm_name = 'first-vm'
    _test_vapp_first_vm_network_adapter_type = NetworkAdapterType.VMXNET3
    _test_vapp_href = None
    _test_vapp_first_vm_href = None

    _non_existent_vm_name = 'non_existent_vm_' + str(uuid1())

    _empty_vapp_name = 'empty_vApp_' + str(uuid1())
    _empty_vapp_description = 'empty vApp description'
    _empty_vapp_runtime_lease = 86400  # in seconds
    _empty_vapp_storage_lease = 86400  # in seconds
    _empty_vapp_owner_name = None
    _empty_vapp_href = None

    _target_vm_name = 'targetvm'

    _idisk_name = 'SCSI'
    _idisk_size = '5242880'
    _idisk_description = '5Mb SCSI disk'

    _computer_name = 'testvm1'
    _boot_delay = 0
    _enter_bios_setup = False
    _description = ''
    _vm_name_update = 'VMupdatedname'
    _description_update = 'Description after update'
    _computer_name_update = 'mycom'
    _boot_delay_update = 60
    _enter_bios_setup_update = True

    _test_vapp_vmtools_name = 'test_vApp_vmtools_' + str(uuid1())
    _test_vapp_vmtools_vm_name = 'yVM'

    _vapp_network_name = 'vapp_network_' + str(uuid1())
    _vapp_network_description = 'Test vApp network'
    _vapp_network_cidr = '90.80.70.1/24'
    _vapp_network_dns1 = '8.8.8.8'
    _vapp_network_dns2 = '8.8.8.9'
    _vapp_network_dns_suffix = 'example.com'
    _vapp_network_ip_range = '90.80.70.2-90.80.70.100'
    _start_ip_vapp_network = '10.100.12.1'
    _end_ip_vapp_network = '10.100.12.100'

    def test_0000_setup(self):
        """Setup the vms required for the other tests in this module.

        Create a vApp with just one vm as per the configuration stated above.

        This test passes if the vApp and vm hrefs are not None.
        """
        logger = Environment.get_default_logger()
        TestVM._client = Environment.get_client_in_default_org(
            TestVM._test_runner_role)
        TestVM._sys_admin_client = Environment.get_sys_admin_client()
        vdc = Environment.get_test_vdc(TestVM._client)
        TestVM._media_resource = Environment.get_test_media_resource()

        logger.debug('Creating vApp ' + TestVM._test_vapp_name + '.')
        TestVM._test_vapp_href = create_customized_vapp_from_template(
            client=TestVM._client,
            vdc=vdc,
            name=TestVM._test_vapp_name,
            catalog_name=Environment.get_default_catalog_name(),
            template_name=Environment.get_default_template_name(),
            memory_size=TestVM._test_vapp_first_vm_memory_size,
            num_cpu=TestVM._test_vapp_first_vm_num_cpu,
            disk_size=TestVM._test_vapp_first_vm_first_disk_size,
            vm_name=TestVM._test_vapp_first_vm_name,
            nw_adapter_type=TestVM._test_vapp_first_vm_network_adapter_type)

        self.assertIsNotNone(TestVM._test_vapp_href)

        vapp = VApp(TestVM._client, href=TestVM._test_vapp_href)
        TestVM._test_vapp = vapp
        vm_resource = vapp.get_vm(TestVM._test_vapp_first_vm_name)
        TestVM._test_vapp_first_vm_href = vm_resource.get('href')

        self.assertIsNotNone(TestVM._test_vapp_first_vm_href)

        logger.debug('Creating empty vApp.')
        TestVM._empty_vapp_href = \
            create_empty_vapp(client=TestVM._client,
                              vdc=vdc,
                              name=TestVM._empty_vapp_name,
                              description=TestVM._empty_vapp_description)
        TestVM._empty_vapp_owner_name = Environment. \
            get_username_for_role_in_test_org(TestVM._test_runner_role)

        #Create independent disk
        TestVM._idisk = vdc.create_disk(name=self._idisk_name,
                                 size=self._idisk_size,
                                 description=self._idisk_description)

        # Upload template with vm tools.
        catalog_author_client = Environment.get_client_in_default_org(
            CommonRoles.CATALOG_AUTHOR)
        org_admin_client = Environment.get_client_in_default_org(
            CommonRoles.ORGANIZATION_ADMINISTRATOR)
        org = Environment.get_test_org(org_admin_client)
        catalog_name = Environment.get_config()['vcd']['default_catalog_name']
        catalog_items = org.list_catalog_items(catalog_name)
        template_name = Environment.get_config()['vcd'][
            'default_template_vmtools_file_name']
        catalog_item_flag = False
        for item in catalog_items:
            if item.get('name').lower() == template_name.lower():
                logger.debug('Reusing existing template ' +
                             template_name)
                catalog_item_flag = True
                break
        if not catalog_item_flag:
            logger.debug('Uploading template ' + template_name +
                         ' to catalog ' + catalog_name + '.')
            org.upload_ovf(catalog_name=catalog_name, file_name=template_name)
            # wait for the template import to finish in vCD.
            catalog_item = org.get_catalog_item(
                name=catalog_name, item_name=template_name)
            template = catalog_author_client.get_resource(
                catalog_item.Entity.get('href'))
            catalog_author_client.get_task_monitor().wait_for_success(
                task=template.Tasks.Task[0])
        # Create Vapp with template of vmware tools
        logger.debug('Creating vApp ' + TestVM._test_vapp_vmtools_name + '.')
        TestVM._test_vapp_vmtools_href = create_customized_vapp_from_template(
            client=TestVM._client,
            vdc=vdc,
            name=TestVM._test_vapp_vmtools_name,
            catalog_name=catalog_name,
            template_name=template_name)
        self.assertIsNotNone(TestVM._test_vapp_href)
        vapp = VApp(TestVM._client, href=TestVM._test_vapp_vmtools_href)
        TestVM._test_vapp_vmtools = vapp
        vm_resource = vapp.get_vm(TestVM._test_vapp_vmtools_vm_name)
        TestVM._test_vapp_vmtools_vm_href = vm_resource.get('href')
        self.assertIsNotNone(TestVM._test_vapp_vmtools_vm_href)

        resource = TestVM._sys_admin_client.get_extension()
        result = TestVM._sys_admin_client.get_linked_resource(
            resource, RelationType.DOWN,
            EntityType.DATASTORE_REFERENCES.value)
        if hasattr(result, '{' + NSMAP['vcloud'] + '}Reference'):
            for reference in result['{' + NSMAP['vcloud'] + '}Reference']:
                TestVM._datastore_href = reference.get('href')
                break

        vapp = Environment.get_vapp_in_test_vdc(
            client=TestVM._client, vapp_name=TestVM._test_vapp_name)
        logger.debug('Creating a vApp network in ' +
                     TestVM._test_vapp_name)
        task = vapp.create_vapp_network(
            TestVM._vapp_network_name, TestVM._vapp_network_cidr,
            TestVM._vapp_network_description, TestVM._vapp_network_dns1,
            TestVM._vapp_network_dns2, TestVM._vapp_network_dns_suffix,
            [TestVM._vapp_network_ip_range])
        result = TestVM._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        vapp.reload()



    def test_0320_list_vm_capabilties(self):
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_vmtools_vm_href)
        dict = vm.list_vm_capabilities()
        self.assertTrue(len(dict) > 0)

    def test_0330_update_vm_capabilities(self):
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_vmtools_vm_href)
        task = vm.update_vm_capabilities_section(memory_hot_add_enabled=False)
        result = TestVM._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        vm_capabilities_section = vm.get_vm_capabilities_section()
        self.assertFalse(vm_capabilities_section.MemoryHotAddEnabled)

    def test_0320_list_vm_capabilties(self):
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_vmtools_vm_href)
        dict = vm.list_vm_capabilities()
        self.assertTrue(len(dict) > 0)

    def test_0330_update_vm_capabilities(self):
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_vmtools_vm_href)
        task = vm.update_vm_capabilities_section(memory_hot_add_enabled=False)
        result = TestVM._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        vm_capabilities_section = vm.get_vm_capabilities_section()
        self.assertFalse(vm_capabilities_section.MemoryHotAddEnabled)

    @developerModeAware
    def test_9998_teardown(self):
        """Delete the vApp created during setup.
        This test passes if the task for deleting the vApp succeed.
        """
        vapps_to_delete = []
        if TestVM._test_vapp_href is not None:
            vapps_to_delete.append(TestVM._test_vapp_name)
            vapp = VApp(TestVM._client, href=TestVM._test_vapp_href)
            if vapp.is_powered_on():
                task = vapp.power_off()
                TestVM._client.get_task_monitor().wait_for_success(task)
                task = vapp.undeploy()
                TestVM._client.get_task_monitor().wait_for_success(task)

        if TestVM._empty_vapp_href is not None:
            vapps_to_delete.append(TestVM._empty_vapp_name)

        if TestVM._test_vapp_vmtools_href is not None:
            vapps_to_delete.append(TestVM._test_vapp_vmtools_name)
            vapp = VApp(TestVM._client, href=TestVM._test_vapp_vmtools_href)
            if vapp.is_powered_on():
                task = vapp.power_off()
                TestVM._client.get_task_monitor().wait_for_success(task)
                task = vapp.undeploy()
                TestVM._client.get_task_monitor().wait_for_success(task)

        vdc = Environment.get_test_vdc(TestVM._sys_admin_client)
        vdc.delete_disk(name=self._idisk_name)
        vdc = Environment.get_test_vdc(TestVM._client)
        for vapp_name in vapps_to_delete:
            task = vdc.delete_vapp(name=vapp_name, force=True)
            result = TestVM._client.get_task_monitor().wait_for_success(task)
            self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_9999_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestVM._client.logout()


if __name__ == '__main__':
    unittest.main()
