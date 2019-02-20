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

from pyvcloud.vcd.client import IpAddressMode
from pyvcloud.vcd.client import NetworkAdapterType
from pyvcloud.vcd.client import TaskStatus
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

    def test_0000_setup(self):
        """Setup the vms required for the other tests in this module.

        Create a vApp with just one vm as per the configuration stated above.

        This test passes if the vApp and vm hrefs are not None.
        """
        logger = Environment.get_default_logger()
        TestVM._client = Environment.get_client_in_default_org(
            TestVM._test_runner_role)
        vdc = Environment.get_test_vdc(TestVM._client)

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
        vm_resource = vapp.get_vm(TestVM._test_vapp_first_vm_name)
        TestVM._test_vapp_first_vm_href = vm_resource.get('href')

        self.assertIsNotNone(TestVM._test_vapp_first_vm_href)

    def test_0010_list_vms(self):
        """Test the method VApp.get_all_vms().

        This test passes if the retrieved vms contain the vm created during
        setup.
        """
        vapp = VApp(TestVM._client, href=TestVM._test_vapp_href)
        vm_resources = vapp.get_vm(TestVM._test_vapp_first_vm_name)

        for vm_resource in vm_resources:
            if vm_resource.get('name') == TestVM._test_vapp_first_vm_name and\
               vm_resource.get('href') == TestVM._test_vapp_first_vm_href:
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

    @unittest.skip("Faulty implementation.")
    def test_0040_get_vc(self):
        """Test the method VM.get_vc().

        This test passes if the retrieved vc name matches with the expected
        vc name.
        """
        vm = VM(TestVM._client, href=TestVM._test_vapp_first_vm_href)
        retrieved_vc_name = vm.get_vc()

        expected_vc_name = Environment.get_config()['vc']['vcenter_host_name']

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
        result = TestVM._client.get_task_monitor().wait_for_success(task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

        # VM.snapshot_revert_to_current
        logger.debug('Reverting vm ' + vm_name + ' to it\'s snapshot.')
        vm.reload()
        task = vm.snapshot_revert_to_current()
        result = TestVM._client.get_task_monitor().wait_for_success(task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

        # VM.snapshot_remove_all()
        logger.debug('Removing all snapshots of vm ' + vm_name)
        vm.reload()
        task = vm.snapshot_remove_all()
        result = TestVM._client.get_task_monitor().wait_for_success(task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0080_vm_nic_operations(self):
        """Test the method add_nic vm.py.

        This test passes if a nic is created successfully.
        """
        vm = VM(TestVM._client, href=TestVM._test_vapp_first_vm_href)
        task = vm.add_nic(NetworkAdapterType.E1000.value, True, True, 'none',
                          IpAddressMode.NONE.value, None)
        result = TestVM._client.get_task_monitor().wait_for_success(task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        vm.reload()
        self.assertTrue(len(vm.list_nics()) == 2)

    @developerModeAware
    def test_9998_teardown(self):
        """Delete the vApp created during setup.

        This test passes if the task for deleting the vApp succeed.
        """
        vapps_to_delete = []
        if TestVM._test_vapp_href is not None:
            vapps_to_delete.append(TestVM._test_vapp_name)

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
