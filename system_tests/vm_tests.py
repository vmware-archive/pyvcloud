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
from pyvcloud.vcd.client import MetadataDomain
from pyvcloud.vcd.client import MetadataVisibility
from pyvcloud.vcd.client import NetworkAdapterType
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.client import TaskStatus
from pyvcloud.vcd.client import VmNicProperties
from pyvcloud.vcd.exceptions import EntityNotFoundException
from pyvcloud.vcd.utils import metadata_to_dict
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
    _metadata_key = 'key_' + str(uuid1())
    _metadata_value = 'value_' + str(uuid1())
    _metadata_new_value = 'new_value_' + str(uuid1())
    _non_existent_metadata_key = 'non_existent_key_' + str(uuid1())

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

        # Create independent disk
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
                if reference.get('name') == 'shared-disk-2':
                    TestVM._datastore_id = reference.get('id')
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

    def test_0010_list_vms(self):
        """Test the method VApp.get_all_vms().
        This test passes if the retrieved vms contain the vm created during
        setup.
        """
        vapp = VApp(TestVM._client, href=TestVM._test_vapp_href)
        vm_resources = vapp.get_vm(TestVM._test_vapp_first_vm_name)
        for vm_resource in vm_resources:
            if vm_resource.get(
                    'name') == TestVM._test_vapp_first_vm_name and \
                    vm_resource.get(
                        'href') == TestVM._test_vapp_first_vm_href:
                return
        self.fail('Retrieved vm list doesn\'t contain vm ' +
                  TestVM._test_vapp_first_vm_name)

    def test_0020_get_vm(self):
        """Test the method VApp.get_vm().
        This test passes if the retrieved vm's name and href matches with the
        expected values.
        """
        vapp = VApp(TestVM._client, href=TestVM._test_vapp_href)
        vm_resource = vapp.get_vm(TestVM._test_vapp_first_vm_name)
        self.assertEqual(TestVM._test_vapp_first_vm_name,
                         vm_resource.get('name'))
        self.assertEqual(TestVM._test_vapp_first_vm_href,
                         vm_resource.get('href'))

    def test_0030_get_non_existent_vm(self):
        """Test the method VApp.get_vm().
        This test passes if the non-existent vm can't be successfully retrieved
        by name.
        """
        vapp = VApp(TestVM._client, href=TestVM._test_vapp_href)
        try:
            vapp.get_vm(TestVM._non_existent_vm_name)
            self.fail('Should not be able to fetch vm ' +
                      TestVM._non_existent_vm_name)
        except EntityNotFoundException:
            return

    def test_0040_get_vc(self):
        """Test the method VM.get_vc().
        This test passes if the retrieved vc name matches with the expected
        vc name.
        """
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_first_vm_href)
        retrieved_vc_name = vm.get_vc()
        expected_vc_name = Environment.get_config()['vc'][
            'vcenter_host_name']
        self.assertEqual(retrieved_vc_name, expected_vc_name)

        # TODO(): Test VApp.connect_vm, VApp.get_vm_moid, VApp.get_primary_ip,
        # VApp.get_admin_password, VApp.add_disk_to_vm once we have more info on
        # how to test these functions.

    def test_0050_customize_vm(self):
        """Test the methods to update and retrieve memory and cpu of a vm.
        The test passes if the update operations are successful and the values
        retrieved thereafter matches the expected values.
        """
        logger = Environment.get_default_logger()
        vm_name = TestVM._test_vapp_first_vm_name
        vm = VM(TestVM._client, href=TestVM._test_vapp_first_vm_href)
        old_num_cpu_data = vm.get_cpus()
        self.assertEqual(old_num_cpu_data['num_cpus'],
                         TestVM._test_vapp_first_vm_num_cpu)
        old_memory_size = vm.get_memory()
        self.assertEqual(old_memory_size,
                         TestVM._test_vapp_first_vm_memory_size)
        # vm can be updated only when it's powered off
        if not vm.is_powered_off():
            task = vm.power_off()
            TestVM._client.get_task_monitor().wait_for_success(task)
            vm.reload()
        logger.debug('Updating number of cpus of vm ' + vm_name + ' to ' +
                     str(TestVM._test_vapp_first_vm_new_num_cpu))
        task = vm.modify_cpu(
            virtual_quantity=TestVM._test_vapp_first_vm_new_num_cpu)
        result = TestVM._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        vm.reload()
        new_num_cpu_data = vm.get_cpus()
        self.assertEqual(new_num_cpu_data['num_cpus'],
                         TestVM._test_vapp_first_vm_new_num_cpu)
        logger.debug('Updating memory size of vm ' + vm_name + ' to ' +
                     str(TestVM._test_vapp_first_vm_new_memory_size))
        task = vm.modify_memory(TestVM._test_vapp_first_vm_new_memory_size)
        result = TestVM._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        vm.reload()
        new_memory_size = vm.get_memory()
        self.assertEqual(new_memory_size,
                         TestVM._test_vapp_first_vm_new_memory_size)
        # power the vm back on
        task = vm.power_on()
        TestVM._client.get_task_monitor().wait_for_success(task)

    def test_0060_vm_power_operations(self):
        """Test the method related to power operations in vm.py.
        This test passes if all the power operations are successful.
        """
        logger = Environment.get_default_logger()
        vm_name = TestVM._test_vapp_first_vm_name
        vm = VM(client=TestVM._client, href=TestVM._test_vapp_first_vm_href)
        # make sure the vm is powered on before running tests
        logger.debug('Making sure vm ' + vm_name + ' is powered on.')
        if vm.is_suspended():
            task = vm.deploy()
            TestVM._client.get_task_monitor().wait_for_success(task=task)
            vm.reload()
        if not vm.is_powered_on():
            task = vm.power_on()
            TestVM._client.get_task_monitor().wait_for_success(task=task)
            vm.reload()
        logger.debug('Un-deploying vm ' + vm_name)
        task = vm.undeploy()
        result = TestVM._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        logger.debug('Deploying vm ' + vm_name)
        vm.reload()
        task = vm.deploy(power_on=False)
        result = TestVM._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        logger.debug('Powering on vm ' + vm_name)
        vm.reload()
        task = vm.power_on()
        result = TestVM._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        logger.debug('Reseting (power) vm ' + vm_name)
        vm.reload()
        task = vm.power_reset()
        result = TestVM._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        logger.debug('Powering off vm ' + vm_name)
        vm.reload()
        task = vm.power_off()
        result = TestVM._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        logger.debug('Powering back on vm ' + vm_name)
        vm.reload()
        task = vm.power_on()
        result = TestVM._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        #       discard suspend state sometime show inconsistent behavior and puts
        #       VM in partially suspended state. Commenting theis scenerio to avoid
        #       this failure.
        #        logger.debug('Suspend a vm ' + vm_name)
        #        vm.reload()
        #        task = vm.suspend()
        #       result = TestVM._client.get_task_monitor().wait_for_success(task)
        #        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        #        logger.debug('Discard suspended state of a vm ' + vm_name)
        #        vm.reload()
        #        if vm.is_suspended():
        #            task = vm.discard_suspended_state()
        #            result = TestVM._client.get_task_monitor().wait_for_success(task)
        #            self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        #        logger.debug('Powering back on vm ' + vm_name)
        vm.reload()
        if not vm.is_powered_on():
            task = vm.power_on()
            result = TestVM._client.get_task_monitor().wait_for_success(
                task)
            self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        # We will need to skip the next two operations, because the vm in
        # question doesn't have vmware tools installed.
        # TODO() : Use a vApp template in which vmware tools are installed
        # on the VM.
        # The reboot operation will fail with the following message
        # -Failed to reboot guest os for the VM "testvm1-p2oH" as required VM
        # tools were found unavailable.
        # logger.debug('Rebooting (power) vm ' + vm_name)
        # vm.reload()
        # task = vm.reboot()
        # result = TestVM._client.get_task_monitor().wait_for_success(task)
        # self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        # The shutdown operation will fail with the following message
        # - Cannot complete operation because VMware Tools is not running in
        # this virtual machine.
        # logger.debug('Shutting down vm ' + vm_name)
        # vm.reload()
        # task = vm.shutdown()
        # result = TestVM._client.get_task_monitor().wait_for_success(task)
        # self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        # end state of vm is deployed and powered on.

    def test_0061_install_vmware_tools(self):
        """Test the method related to install vmware tools in vm.py.
        This test passes if install vmware tools operation is successful.
        """
        logger = Environment.get_default_logger()
        vm_name = TestVM._test_vapp_first_vm_name
        vm = VM(TestVM._client, href=TestVM._test_vapp_first_vm_href)
        logger.debug('Installing Vmware Tools in VM:  ' + vm_name)
        task = vm.install_vmware_tools()
        result = TestVM._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0062_insert_cd(self):
        """Test the method related to insert CD in vm.py.
        This test passes if insert CD operation is successful.
        """
        logger = Environment.get_default_logger()
        vm_name = TestVM._test_vapp_first_vm_name
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_first_vm_href)
        media_id = TestVM._media_resource.Entity.get('id')
        logger.debug('Inserting CD in VM:  ' + vm_name)
        id = media_id.split(':')[3]
        task = vm.insert_cd_from_catalog(media_id=id)
        result = TestVM._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0063_eject_cd(self):
        """Test the method related to eject CD in vm.py.
        This test passes if eject CD operation is successful.
        """
        logger = Environment.get_default_logger()
        vm_name = TestVM._test_vapp_first_vm_name
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_first_vm_href)
        media_id = TestVM._media_resource.Entity.get('id')
        logger.debug('Ejecting CD from VM:  ' + vm_name)
        id = media_id.split(':')[3]
        task = vm.eject_cd(media_id=id)
        result = TestVM._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0070_vm_snapshot_operations(self):
        """Test the method related to snapshot operations in vm.py.
        This test passes if all the snapshot operations are successful.
        """
        logger = Environment.get_default_logger()
        vm_name = TestVM._test_vapp_first_vm_name
        vm = VM(TestVM._client, href=TestVM._test_vapp_first_vm_href)
        # VM.snapshot_create()
        logger.debug('Creating snapshot of vm ' + vm_name)
        task = vm.snapshot_create(memory=False, quiesce=False)
        result = TestVM._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        # VM.snapshot_revert_to_current
        logger.debug('Reverting vm ' + vm_name + ' to it\'s snapshot.')
        vm.reload()
        task = vm.snapshot_revert_to_current()
        result = TestVM._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        # VM.snapshot_remove_all()
        logger.debug('Removing all snapshots of vm ' + vm_name)
        vm.reload()
        task = vm.snapshot_remove_all()
        result = TestVM._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0071_consolidate(self):
        """Test the method related to consolidate in vm.py.
        This test passes if consolidate operation is successful.
        """
        logger = Environment.get_default_logger()
        vm_name = TestVM._test_vapp_first_vm_name
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_first_vm_href)
        vm.reload()
        if vm.is_powered_on():
            task = vm.power_off()
            result = TestVM._sys_admin_client. \
                get_task_monitor().wait_for_success(task)
            self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        vm.reload()
        logger.debug('Consolidating VM:  ' + vm_name)
        task = vm.consolidate()
        result = TestVM._sys_admin_client. \
            get_task_monitor().wait_for_success(task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0072_copy_to(self):
        """Test the method related to copy VM from one vapp to another.
        This test passes if copy VM operation is successful.
        """
        target_vapp_name = TestVM._empty_vapp_name
        source_vapp_name = TestVM._test_vapp_name
        target_vm_name = TestVM._target_vm_name
        vm = VM(TestVM._client, href=TestVM._test_vapp_first_vm_href)
        task = vm.copy_to(source_vapp_name=source_vapp_name,
                          target_vapp_name=target_vapp_name,
                          target_vm_name=target_vm_name)
        result = TestVM._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0073_move_to(self):
        """Test the method related to move VM from one vapp to another.
        This test passes if move VM operation is successful.
        """
        target_vapp_name = TestVM._test_vapp_name
        source_vapp_name = TestVM._empty_vapp_name
        target_vm_name = TestVM._target_vm_name
        vapp = VApp(TestVM._client, href=TestVM._empty_vapp_href)
        vm_resource = vapp.get_vm(TestVM._target_vm_name)
        TestVM._target_vm_href = vm_resource.get('href')
        vm = VM(TestVM._client, href=TestVM._target_vm_href)
        task = vm.move_to(source_vapp_name=source_vapp_name,
                          target_vapp_name=target_vapp_name,
                          target_vm_name=target_vm_name)
        result = TestVM._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0074_delete_vm(self):
        """Test the method related to delete VM.
        This test passes if delete VM operation is successful.
        """
        vapp = VApp(TestVM._client, href=TestVM._test_vapp_href)
        vm_resource = vapp.get_vm(TestVM._target_vm_name)
        TestVM._target_vm_href = vm_resource.get('href')
        vm = VM(TestVM._client, href=TestVM._target_vm_href)
        task = vm.delete()
        result = TestVM._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0080_vm_nic_operations(self):
        """Test the method add_nic and list_nics vm.py.
        This test passes if a nic is created successfully.
        """
        vm = VM(TestVM._client, href=TestVM._test_vapp_first_vm_href)
        task = vm.add_nic(NetworkAdapterType.E1000.value, True, True,
                          TestVM._vapp_network_name,
                          IpAddressMode.POOL.value, None)
        result = TestVM._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        vm.reload()
        self.assertTrue(len(vm.list_nics()) == 2)

    def test_0085_vm_nic_update(self):
        vm = VM(TestVM._client, href=TestVM._test_vapp_first_vm_href)
        task = vm.update_nic(network_name=TestVM._vapp_network_name,
                             is_connected=False)
        result = TestVM._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0090_vm_nic_delete(self):
        """Test the method delete_nic in vm.py
        This test passes if a nic is deleted successfully.
        """
        vm = VM(TestVM._client, href=TestVM._test_vapp_first_vm_href)
        nics = vm.list_nics()
        self.assertTrue(len(nics) == 2)
        nic_to_delete = next(i[VmNicProperties.INDEX.value] for i in nics
                             if i[VmNicProperties.PRIMARY.value])
        task = vm.delete_nic(nic_to_delete)
        result = TestVM._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        vm.reload()
        self.assertTrue(len(vm.list_nics()) == 1)

    def test_0100_upgrade_virtual_hardware(self):
        vm = VM(TestVM._client, href=TestVM._test_vapp_first_vm_href)
        task = vm.upgrade_virtual_hardware()
        result = TestVM._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0110_attach_independent_disk(self):
        vdc = Environment.get_test_vdc(TestVM._client)
        idisk = vdc.get_disk(name=TestVM._idisk_name)
        task = TestVM._test_vapp. \
            attach_disk_to_vm(disk_href=idisk.get('href'),
                              vm_name=TestVM._test_vapp_first_vm_name)
        result = TestVM._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        is_disk_attached = self.__validate_is_attached_disk(
            is_disk_attached=False)
        self.assertTrue(is_disk_attached)

    def test_0120_detach_independent_disk(self):
        vdc = Environment.get_test_vdc(TestVM._client)
        idisk = vdc.get_disk(name=TestVM._idisk_name)
        task = TestVM._test_vapp. \
            detach_disk_from_vm(disk_href=idisk.get('href'),
                                vm_name=TestVM._test_vapp_first_vm_name)
        result = TestVM._client.get_task_monitor().wait_for_success(
            task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        is_disk_attached = self.__validate_is_attached_disk(
            is_disk_attached=False)
        self.assertFalse(is_disk_attached)

    def test_0130_general_setting_detail(self):
        vm = VM(TestVM._client, href=TestVM._test_vapp_first_vm_href)
        result = vm.general_setting_detail()
        self.assertNotEqual(len(result), 0)

    def test_0140_list_storage_profile(self):
        vm = VM(TestVM._client, href=TestVM._test_vapp_first_vm_href)
        result = vm.list_storage_profile()
        self.assertNotEqual(len(result), 0)

    def __validate_is_attached_disk(self, is_disk_attached=False):
        vm = VM(TestVM._client, href=TestVM._test_vapp_first_vm_href)
        vm.reload()
        vm_resource = vm.get_resource()
        disk_list = TestVM._client.get_resource(
            vm_resource.get('href') + '/virtualHardwareSection/disks')
        for disk in disk_list.Item:
            if disk['{' + NSMAP['rasd'] + '}Description'] == 'Hard disk':
                if disk.xpath('rasd:HostResource', namespaces=NSMAP)[
                    0].attrib.get('{' + NSMAP['vcloud'] + '}disk'):
                    is_disk_attached = True
                    break
        return is_disk_attached

    def test_0150_reload_from_vc(self):
        """Test the method related to reload_from_vc in vm.py.
        This test passes if reload from VC operation is successful.
        """
        logger = Environment.get_default_logger()
        vm_name = TestVM._test_vapp_first_vm_name
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_first_vm_href)
        vm.reload()
        logger.debug('Reloading VM:  ' + vm_name + ' from VC.')
        task = vm.reload_from_vc()
        result = TestVM._sys_admin_client. \
            get_task_monitor().wait_for_success(task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0160_check_compliance(self):
        """Test the method related to check_compliance in vm.py.
        This test passes if check compliance operation is successful.
        """
        logger = Environment.get_default_logger()
        vm_name = TestVM._test_vapp_first_vm_name
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_first_vm_href)
        vm.reload()
        logger.debug('Checking compliance of VM:  ' + vm_name)
        task = vm.check_compliance()
        result = TestVM._sys_admin_client. \
            get_task_monitor().wait_for_success(task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0170_customize_at_next_power_on(self):
        """Test the method related to customize_at_next_power_on in vm.py.
        This test passes if customize at next power on operation is successful.
        """
        logger = Environment.get_default_logger()
        vm_name = TestVM._test_vapp_first_vm_name
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_first_vm_href)
        vm.reload()
        vm.customize_at_next_power_on()
        task = vm.power_on()
        TestVM._sys_admin_client. \
            get_task_monitor().wait_for_success(task=task)
        status = vm.get_guest_customization_status()
        self.assertEqual(status, 'GC_PENDING')

    def test_0180_update_general_setting(self):
        """Test the method related to update general setting in vm.py.
        This test passes if general setting update successful.
        """
        vm_name = TestVM._test_vapp_first_vm_name
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_first_vm_href)
        vm.reload()
        # Updating general setting of vm
        task = vm.update_general_setting(
            name=TestVM._vm_name_update,
            description=TestVM._description_update,
            computer_name=TestVM._computer_name_update,
            boot_delay=TestVM._boot_delay_update,
            enter_bios_setup=TestVM._enter_bios_setup_update)
        result = TestVM._sys_admin_client. \
            get_task_monitor().wait_for_success(task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        vm.reload()
        result = vm.general_setting_detail()
        self.assertEqual(result['Name'], TestVM._vm_name_update)
        self.assertEqual(result['Description'], TestVM._description_update)
        self.assertEqual(result['Computer Name'],
                         TestVM._computer_name_update)
        self.assertEqual(result['Boot Delay'], TestVM._boot_delay_update)
        self.assertEqual(result['Enter BIOS Setup'],
                         TestVM._enter_bios_setup_update)
        # Reverting back general setting of vm
        task = vm.update_general_setting(
            name=TestVM._test_vapp_first_vm_name,
            description=TestVM._description,
            computer_name=TestVM._computer_name,
            boot_delay=TestVM._boot_delay,
            enter_bios_setup=TestVM._enter_bios_setup)
        result = TestVM._sys_admin_client. \
            get_task_monitor().wait_for_success(task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0190_enable_gc(self):
        """Test the method related to enable_guest_customization in vm.py.
        This test passes if enable GC operation is successful.
        """
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_vmtools_vm_href)
        # Power off VM
        task = vm.power_off()
        TestVM._sys_admin_client. \
            get_task_monitor().wait_for_success(task=task)
        vm.reload()
        task = vm.enable_guest_customization(is_enabled=True)
        TestVM._sys_admin_client. \
            get_task_monitor().wait_for_success(task=task)
        vm.reload()
        gc_section = vm.get_guest_customization_section()
        self.assertTrue(gc_section.Enabled)

    def test_0200_get_gc_status(self):
        """Test the method related to get_guest_customization_status in vm.py.
        This test passes if it gives guest customization status.
        """
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_vmtools_vm_href)
        status = vm.get_guest_customization_status()
        self.assertEqual(status, 'GC_PENDING')

    def test_0210_poweron_and_force_recustomization(self):
        """Test the method related to power_on_and_force_recustomization in
        vm.py. This test passes if force customization at power on operation is
        successful.
        """
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_vmtools_vm_href)
        if vm.is_powered_on():
            task = vm.power_off()
            TestVM._sys_admin_client. \
                get_task_monitor().wait_for_success(task=task)
        task = vm.undeploy()
        TestVM._sys_admin_client. \
            get_task_monitor().wait_for_success(task=task)
        vm.reload()
        task = vm.power_on_and_force_recustomization()
        result = TestVM._sys_admin_client. \
            get_task_monitor().wait_for_success(task=task)
        status = vm.get_guest_customization_status()
        self.assertEqual(status, 'GC_PENDING')

    def test_0220_list_virtual_harware_section(self):
        vm = VM(TestVM._client, href=TestVM._test_vapp_first_vm_href)
        list = vm.list_virtual_hardware_section(is_disk=True, is_media=True,
                                                is_networkCards=True)
        self.assertTrue(len(list) > 0)

    def test_0230_get_compliance_result(self):
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_first_vm_href)
        result = vm.get_compliance_result()
        self.assertEqual(result.ComplianceStatus, 'COMPLIANT')

    def test_0240_list_all_current_metrics(self):
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_first_vm_href)
        list = vm.list_all_current_metrics()
        self.assertTrue(len(list) > 0)

    def test_0250_list_subset_current_metrics(self):
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_first_vm_href)
        list = vm.list_current_metrics_subset(metric_pattern='*.average')
        self.assertTrue(len(list) > 0)

    def test_0260_relocate(self):
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_first_vm_href)
        datastore_id = TestVM._datastore_id
        id = datastore_id.split(':')[3]
        task = vm.relocate(datastore_id=id)
        result = TestVM._sys_admin_client. \
            get_task_monitor().wait_for_success(task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0270_list_os_info(self):
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_first_vm_href)
        dict = vm.list_os_section()
        self.assertTrue(len(dict) > 0)

    """Commenting test case as it shows inconsistent behavior for task
    object in CI/CD.
    def test_0280_update_os_section(self):
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_first_vm_href)
        task = vm.update_operating_system_section(ovf_info="new os")
        result = TestVM._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)"""

    def test_0290_list_gc_info(self):
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_vmtools_vm_href)
        dict = vm.list_gc_section()
        self.assertTrue(len(dict) > 0)

    def test_0300_update_gc_section(self):
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_vmtools_vm_href)
        task = vm.update_guest_customization_section(enabled=True)
        result = TestVM._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        gc_section = vm.get_guest_customization_section()
        self.assertTrue(gc_section.Enabled)

    def test_0310_get_post_gc_status(self):
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_vmtools_vm_href)
        dict = vm.list_check_post_gc_status()
        self.assertTrue(len(dict) > 0)

    def test_0320_list_vm_capabilties(self):
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_vmtools_vm_href)
        dict = vm.list_vm_capabilities()
        self.assertTrue(len(dict) > 0)

    def test_0330_update_vm_capabilities(self):
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_vmtools_vm_href)
        task = vm.update_vm_capabilities_section(
            memory_hot_add_enabled=False)
        result = TestVM._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        vm_capabilities_section = vm.get_vm_capabilities_section()
        self.assertFalse(vm_capabilities_section.MemoryHotAddEnabled)

    def test_0340_list_boot_options(self):
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_vmtools_vm_href)
        dict = vm.list_boot_options()
        self.assertTrue(len(dict) > 0)

    def test_0350_update_boot_options(self):
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_vmtools_vm_href)
        task = vm.update_boot_options(enter_bios_setup=False)
        result = TestVM._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        boot_options = vm.get_boot_options()
        self.assertFalse(boot_options.EnterBIOSSetup)

    def test_0360_list_runtime_info(self):
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_vmtools_vm_href)
        dict = vm.list_run_time_info()
        self.assertTrue(len(dict) > 0)

    def test_0370_set_meadata(self):
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_first_vm_href)
        task = vm.set_metadata(
            domain=MetadataDomain.GENERAL.value,
            visibility=MetadataVisibility.READ_WRITE,
            key=TestVM._metadata_key,
            value=TestVM._metadata_value)
        result = TestVM._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0380_get_meadata(self):
        # retrieve metadata
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_first_vm_href)
        entries = metadata_to_dict(vm.get_metadata())
        self.assertTrue(len(entries) > 0)

    def test_0390_update_metadata(self):
        # update metadata value as org admin
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_first_vm_href)
        task = vm.set_metadata(
            domain=MetadataDomain.GENERAL.value,
            visibility=MetadataVisibility.READ_WRITE,
            key=TestVM._metadata_key,
            value=TestVM._metadata_new_value)
        TestVM._client.get_task_monitor().wait_for_success(task)
        entries = metadata_to_dict(vm.get_metadata())
        self.assertEqual(TestVM._metadata_new_value,
                         entries[TestVM._metadata_key])

    def test_0400_remove_metadata(self):
        # remove metadata entry
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_first_vm_href)
        task = vm.remove_metadata(key=TestVM._metadata_key)
        result = TestVM._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0410_list_screen_ticket(self):
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_vmtools_vm_href)
        if vm.is_powered_off():
            task = vm.deploy(power_on=True)
            TestVM._client.get_task_monitor().wait_for_success(task)
        dict = vm.list_screen_ticket()
        self.assertTrue(len(dict) > 0)

    def test_0420_list_mks_ticket(self):
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_vmtools_vm_href)
        dict = vm.list_mks_ticket()
        self.assertTrue(len(dict) > 0)

    def test_0430_list_product_sections(self):
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_vmtools_vm_href)
        list = vm.list_product_sections()
        self.assertTrue(len(list) > 0)

    def test_0440_update_vhs_disk(self):
        # update vhs disk
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_first_vm_href)
        disk_list = vm.list_virtual_hardware_section(is_cpu=False,
                                                     is_memory=False,
                                                     is_disk=True)
        for disk in disk_list:
            element_name = disk['diskElementName']
            virtual_quantity = disk['diskVirtualQuantityInBytes']
            break
        task = vm.update_vhs_disks(element_name=element_name,
                                   virtual_quatntity_in_bytes=virtual_quantity)
        result = TestVM._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0450_enable_nested_hypervisor(self):
        vapp = VApp(TestVM._client, href=TestVM._test_vapp_href)
        self._power_off_and_undeploy(vapp=vapp)
        vm = VM(TestVM._sys_admin_client,
                href=TestVM._test_vapp_first_vm_href)
        task = vm.enable_nested_hypervisor()
        result = TestVM._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def _power_off_and_undeploy(self, vapp):
        if vapp.is_powered_on():
            task = vapp.power_off()
            TestVM._client.get_task_monitor().wait_for_success(task)
            task = vapp.undeploy()
            TestVM._client.get_task_monitor().wait_for_success(task)

    @developerModeAware
    def test_9998_teardown(self):
        """Delete the vApp created during setup.
        This test passes if the task for deleting the vApp succeed.
        """
        vapps_to_delete = []
        if TestVM._test_vapp_href is not None:
            vapps_to_delete.append(TestVM._test_vapp_name)
            vapp = VApp(TestVM._client, href=TestVM._test_vapp_href)
            self._power_off_and_undeploy(vapp=vapp)

        if TestVM._empty_vapp_href is not None:
            vapps_to_delete.append(TestVM._empty_vapp_name)

        if TestVM._test_vapp_vmtools_href is not None:
            vapps_to_delete.append(TestVM._test_vapp_vmtools_name)
            vapp = VApp(TestVM._client, href=TestVM._test_vapp_vmtools_href)
            self._power_off_and_undeploy(vapp=vapp)

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
