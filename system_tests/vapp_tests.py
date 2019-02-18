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

from pyvcloud.vcd.client import MetadataDomain
from pyvcloud.vcd.client import MetadataVisibility
from pyvcloud.vcd.client import NetworkAdapterType
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import TaskStatus
from pyvcloud.vcd.exceptions import EntityNotFoundException
from pyvcloud.vcd.vapp import VApp
from pyvcloud.vcd.utils import metadata_to_dict


class TestVApp(BaseTestCase):
    """Test vApp functionalities implemented in pyvcloud."""

    _test_runner_role = CommonRoles.VAPP_AUTHOR
    _client = None

    _empty_vapp_name = 'empty_vApp_' + str(uuid1())
    _empty_vapp_description = 'empty vApp description'
    _empty_vapp_runtime_lease = 86400  # in seconds
    _empty_vapp_storage_lease = 86400  # in seconds
    _empty_vapp_owner_name = None
    _empty_vapp_href = None

    _additional_vm_name = 'additional-vm'

    _customized_vapp_name = 'customized_vApp_' + str(uuid1())
    _customized_vapp_description = 'customized vApp description'
    _customized_vapp_num_cpu = 2
    _customized_vapp_memory_size = 64  # MB
    _customized_vapp_disk_size = 100  # MB
    _customized_vapp_vm_name = 'custom-vm'
    _customized_vapp_vm_hostname = 'custom-host'
    _customized_vapp_vm_network_adapter_type = NetworkAdapterType.VMXNET3
    _customized_vapp_owner_name = None
    _customized_vapp_href = None

    _non_existent_vapp_name = 'non_existent_vapp_' + str(uuid1())

    _metadata_key = 'key_' + str(uuid1())
    _metadata_value = 'value_' + str(uuid1())
    _metadata_new_value = 'new_value_' + str(uuid1())
    _non_existent_metadata_key = 'non_existent_key_' + str(uuid1())

    _vapp_network_name = 'vapp_network_' + str(uuid1())
    _vapp_network_description = 'Test vApp network'
    _vapp_network_cidr = '90.80.70.1/24'
    _vapp_network_dns1 = '8.8.8.8'
    _vapp_network_dns2 = '8.8.8.9'
    _vapp_network_dns_suffix = 'example.com'
    _vapp_network_ip_range = '90.80.70.2-90.80.70.100'

    def test_0000_setup(self):
        """Setup the vApps required for the other tests in this module.

        Create two vApps as per the configuration stated above.

        This test passes if the two vApp hrefs are not None.
        """
        logger = Environment.get_default_logger()
        TestVApp._client = Environment.get_client_in_default_org(
            TestVApp._test_runner_role)
        vdc = Environment.get_test_vdc(TestVApp._client)

        logger.debug('Creating empty vApp.')
        TestVApp._empty_vapp_href = \
            create_empty_vapp(client=TestVApp._client,
                              vdc=vdc,
                              name=TestVApp._empty_vapp_name,
                              description=TestVApp._empty_vapp_description)
        TestVApp._empty_vapp_owner_name = Environment.\
            get_username_for_role_in_test_org(TestVApp._test_runner_role)

        logger.debug('Creating customized vApp.')
        TestVApp._customized_vapp_href = create_customized_vapp_from_template(
            client=TestVApp._client,
            vdc=vdc,
            name=TestVApp._customized_vapp_name,
            catalog_name=Environment.get_default_catalog_name(),
            template_name=Environment.get_default_template_name(),
            description=TestVApp._customized_vapp_description,
            memory_size=TestVApp._customized_vapp_memory_size,
            num_cpu=TestVApp._customized_vapp_num_cpu,
            disk_size=TestVApp._customized_vapp_disk_size,
            vm_name=TestVApp._customized_vapp_vm_name,
            vm_hostname=TestVApp._customized_vapp_vm_hostname,
            nw_adapter_type=TestVApp._customized_vapp_vm_network_adapter_type)
        TestVApp._customized_vapp_owner_name = Environment.\
            get_username_for_role_in_test_org(TestVApp._test_runner_role)

        self.assertIsNotNone(TestVApp._empty_vapp_href)
        self.assertIsNotNone(TestVApp._customized_vapp_href)

    def test_0010_get_vapp(self):
        """Test the method vdc.get_vapp().

        This test passes if the expected vApp can be successfully retrieved by
        name.
        """
        vdc = Environment.get_test_vdc(TestVApp._client)
        vapp_resource = vdc.get_vapp(TestVApp._customized_vapp_name)
        self.assertIsNotNone(vapp_resource)

    def test_0011_edit_vapp_name_desc(self):
        """Test the method vapp.edit_name_and_description().

        This test passes if the name and desc of the vapp is changed.
        """
        vapp_resource = Environment.get_vapp_in_test_vdc(
            client=TestVApp._client, vapp_name=TestVApp._customized_vapp_name)
        self.assertIsNotNone(vapp_resource)

        self._update_vapp_name_desc(vapp_resource, 'testname1289', 'testdesc')

        # reset vapp to old name
        self._update_vapp_name_desc(vapp_resource,
                                    TestVApp._customized_vapp_name,
                                    TestVApp._customized_vapp_description)

    def _update_vapp_name_desc(self, vapp, name, desc):
        task = vapp.edit_name_and_description(name, desc)
        result = TestVApp._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

        # verify name, desc
        vapp.reload()
        self.assertEqual(vapp.get_resource().Description.text, desc)
        self.assertEqual(vapp.get_resource().get('name'), name)

    def test_0020_get_nonexistent_vapp(self):
        """Test the method vdc.get_vapp().

        This test passes if the non-existent vApp can't be successfully
        retrieved by name.
        """
        vdc = Environment.get_test_vdc(TestVApp._client)
        try:
            vdc.get_vapp(TestVApp._non_existent_vapp_name)
            self.fail('Should not be able to fetch vApp ' +
                      TestVApp._non_existent_vapp_name)
        except EntityNotFoundException as e:
            return

    def test_0030_add_delete_vm(self):
        """Test the method vapp.add_vms() and vapp.delete_vms().

        This test passes if the supplied vm is sucessfully added to the vApp
        and then successfully removed from the vApp.
        """
        logger = Environment.get_default_logger()
        vapp_name = TestVApp._empty_vapp_name
        vapp = Environment.get_vapp_in_test_vdc(
            client=TestVApp._client, vapp_name=vapp_name)

        source_vapp_name = TestVApp._customized_vapp_name
        source_vapp = Environment.get_vapp_in_test_vdc(
            client=TestVApp._client, vapp_name=source_vapp_name)
        source_vapp_resource = source_vapp.get_resource()
        source_vm_name = TestVApp._customized_vapp_vm_name
        target_vm_name = TestVApp._additional_vm_name
        spec = {
            'vapp': source_vapp_resource,
            'source_vm_name': source_vm_name,
            'target_vm_name': target_vm_name
        }

        logger.debug('Adding vm ' + target_vm_name + ' to vApp ' + vapp_name)
        # deploy and power_on are false to make sure that the subsequent
        # deletion of vm doesn't require additional power operations
        task = vapp.add_vms([spec],
                            deploy=False,
                            power_on=False,
                            all_eulas_accepted=True)
        result = TestVApp._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

        logger.debug('Removing vm ' + target_vm_name + ' from vApp ' +
                     vapp_name)
        vapp.reload()
        task = vapp.delete_vms([target_vm_name])
        result = TestVApp._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0040_customized_vapp(self):
        """Test the correctness of the customization of vdc.instantiate_vapp().

        This test passes if the customized vApp is retrieved successfully
        and it's verified that the vApp is correctly customized as per the
        config in this file.
        """
        vapp_name = TestVApp._customized_vapp_name
        vapp = Environment.get_vapp_in_test_vdc(
            client=TestVApp._client, vapp_name=vapp_name)
        vapp_resource = vapp.get_resource()

        self.assertEqual(vapp_resource.Description.text,
                         TestVApp._customized_vapp_description)

        vms = vapp_resource.xpath(
            '//vcloud:VApp/vcloud:Children/vcloud:Vm', namespaces=NSMAP)
        self.assertTrue(len(vms) >= 1)
        first_vm = vms[0]

        self.assertEqual(
            first_vm.get('name'), TestVApp._customized_vapp_vm_name)

        self.assertEqual(first_vm.GuestCustomizationSection.ComputerName.text,
                         TestVApp._customized_vapp_vm_hostname)

        items = first_vm.xpath(
            '//ovf:VirtualHardwareSection/ovf:Item',
            namespaces={'ovf': NSMAP['ovf']})
        self.assertTrue(len(items) > 0)

        cpu_size = None
        memory_size = None
        disk_size = None
        for item in items:
            if item['{' + NSMAP['rasd'] + '}ResourceType'] == 3:
                cpu_size = item['{' + NSMAP['rasd'] + '}VirtualQuantity']
            elif item['{' + NSMAP['rasd'] + '}ResourceType'] == 4:
                memory_size = item['{' + NSMAP['rasd'] + '}VirtualQuantity']
            elif item['{' + NSMAP['rasd'] + '}ResourceType'] == 17:
                disk_size = item['{' + NSMAP['rasd'] + '}VirtualQuantity']

        self.assertIsNotNone(cpu_size)
        self.assertEqual(cpu_size, TestVApp._customized_vapp_num_cpu)
        self.assertIsNotNone(memory_size)
        self.assertEqual(memory_size, TestVApp._customized_vapp_memory_size)
        self.assertIsNotNone(disk_size)
        self.assertEqual(disk_size,
                         (TestVApp._customized_vapp_disk_size * 1024 * 1024))

    def test_0050_vapp_power_options(self):
        """Test the method related to power operations in vapp.py.

        This test passes if all the power operations are successful.
        """
        logger = Environment.get_default_logger()
        vapp_name = TestVApp._customized_vapp_name
        vapp = Environment.get_vapp_in_test_vdc(
            client=TestVApp._client, vapp_name=vapp_name)

        # make sure the vApp is powered on before running tests
        logger.debug('Making sure vApp ' + vapp_name + ' is powered on.')
        if vapp.is_suspended():
            task = vapp.deploy()
            TestVApp._client.get_task_monitor().wait_for_success(task=task)
            vapp.reload()

        if not vapp.is_powered_on():
            task = vapp.power_on()
            TestVApp._client.get_task_monitor().wait_for_success(task=task)
            vapp.reload()

        logger.debug('Un-deploying vApp ' + vapp_name)
        task = vapp.undeploy()
        result = TestVApp._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

        logger.debug('Deploying vApp ' + vapp_name)
        vapp.reload()
        task = vapp.deploy(power_on=False)
        result = TestVApp._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

        logger.debug('Powering on vApp ' + vapp_name)
        vapp.reload()
        task = vapp.power_on()
        result = TestVApp._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

        logger.debug('Reseting (power) vApp ' + vapp_name)
        vapp.reload()
        task = vapp.power_reset()
        result = TestVApp._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

        logger.debug('Powering off vApp ' + vapp_name)
        vapp.reload()
        task = vapp.power_off()
        result = TestVApp._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

        logger.debug('Powering back on vApp ' + vapp_name)
        vapp.reload()
        task = vapp.power_on()
        result = TestVApp._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

        logger.debug('Rebooting (power) vApp ' + vapp_name)
        vapp.reload()
        task = vapp.reboot()
        result = TestVApp._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

        logger.debug('Shutting down vApp ' + vapp_name)
        vapp.reload()
        task = vapp.shutdown()
        result = TestVApp._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        # end state of vApp is deployed and partially powered on.

    def test_0060_vapp_network_connection(self):
        """Test vapp.connect/disconnect_org_vdc_network().

        This test passes if the connect and disconnect to orgvdc network
        operations are successful.
        """
        logger = Environment.get_default_logger()

        network_name = Environment.get_default_orgvdc_network_name()

        vapp_name = TestVApp._customized_vapp_name
        vapp = Environment.get_vapp_in_test_vdc(
            client=TestVApp._client, vapp_name=vapp_name)

        logger.debug('Connecting vApp ' + vapp_name + ' to orgvdc network ' +
                     network_name)
        task = vapp.connect_org_vdc_network(network_name)
        result = TestVApp._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

        logger.debug('Disconnecting vApp ' + vapp_name +
                     ' to orgvdc network ' + network_name)
        vapp.reload()
        task = vapp.disconnect_org_vdc_network(network_name)
        result = TestVApp._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0070_vapp_acl(self):
        """Test the method related to access control list in vapp.py.

        This test passes if all the acl operations are successful.
        """
        logger = Environment.get_default_logger()
        vapp_name = TestVApp._customized_vapp_name
        vapp = Environment.get_vapp_in_test_vdc(
            client=TestVApp._client, vapp_name=vapp_name)

        vapp_user_name = Environment.get_username_for_role_in_test_org(
            CommonRoles.VAPP_USER)
        console_user_name = Environment.get_username_for_role_in_test_org(
            CommonRoles.CONSOLE_ACCESS_ONLY)

        # remove all
        logger.debug('Removing all access control from vApp ' + vapp_name)
        control_access = vapp.remove_access_settings(remove_all=True)
        self.assertFalse(hasattr(control_access, 'AccessSettings'))

        # add
        logger.debug('Adding 2 access control rule to vApp ' + vapp_name)
        vapp.reload()
        access_settings_list = [{
            'name': console_user_name,
            'type': 'user'
        }, {
            'name': vapp_user_name,
            'type': 'user',
            'access_level': 'Change'
        }]
        control_access = vapp.add_access_settings(access_settings_list)
        self.assertEqual(len(control_access.AccessSettings.AccessSetting), 2)

        # get
        logger.debug('Fetching access control rules for vApp ' + vapp_name)
        vapp.reload()
        control_access = vapp.get_access_settings()
        self.assertEqual(len(control_access.AccessSettings.AccessSetting), 2)

        # remove
        logger.debug('Removing 1 access control rule for vApp ' + vapp_name)
        vapp.reload()
        control_access = vapp.remove_access_settings(
            access_settings_list=[{
                'name': vapp_user_name,
                'type': 'user'
            }])
        self.assertEqual(len(control_access.AccessSettings.AccessSetting), 1)

        # share
        logger.debug('Sharing vApp ' + vapp_name + ' with everyone in the org')
        vapp.reload()
        control_access = vapp.share_with_org_members(
            everyone_access_level='ReadOnly')
        self.assertEqual(control_access.IsSharedToEveryone.text, 'true')
        self.assertEqual(control_access.EveryoneAccessLevel.text, 'ReadOnly')

        # unshare
        logger.debug('Un-sharing vApp ' + vapp_name +
                     ' from everyone in the org')
        vapp.reload()
        control_access = vapp.unshare_from_org_members()
        self.assertEqual(control_access.IsSharedToEveryone.text, 'false')

        # remove all access control rules again
        logger.debug('Removing all access control from vApp ' + vapp_name)
        control_access = vapp.remove_access_settings(remove_all=True)
        self.assertFalse(hasattr(control_access, 'AccessSettings'))

    def test_0080_vapp_lease(self):
        """Test the method vapp.set_lease().

        This test passes if the lease setting operation completes successfully.
        """
        vapp_name = TestVApp._empty_vapp_name
        vapp = Environment.get_vapp_in_test_vdc(
            client=TestVApp._client, vapp_name=vapp_name)

        task = vapp.set_lease(
            deployment_lease=TestVApp._empty_vapp_runtime_lease,
            storage_lease=TestVApp._empty_vapp_storage_lease)
        result = TestVApp._client.get_task_monitor().\
            wait_for_success(task=task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0090_change_vapp_owner(self):
        """Test the method vapp.change_owner().

        This test passes if the owner of the vApp is successfuly changed to the
        desired user.
        """
        try:
            logger = Environment.get_default_logger()
            org_admin_client = Environment.get_client_in_default_org(
                CommonRoles.ORGANIZATION_ADMINISTRATOR)

            vapp_name = TestVApp._empty_vapp_name
            vapp = Environment.get_vapp_in_test_vdc(
                client=org_admin_client, vapp_name=vapp_name)

            vapp_user_name = Environment.get_username_for_role_in_test_org(
                CommonRoles.VAPP_USER)
            vapp_user_href = Environment.get_user_href_in_test_org(
                vapp_user_name)

            logger.debug('Changing owner of vApp ' + vapp_name + ' to ' +
                         vapp_user_name)
            vapp.change_owner(vapp_user_href)
            vapp.reload()
            self.assertEqual(vapp.get_resource().Owner.User.get('name'),
                             vapp_user_name)

            logger.debug('Changing owner of vApp ' + vapp_name + ' back to ' +
                         TestVApp._empty_vapp_owner_name)
            original_owner_href = Environment.get_user_href_in_test_org(
                TestVApp._empty_vapp_owner_name)
            vapp.change_owner(original_owner_href)
            vapp.reload()
            self.assertEqual(vapp.get_resource().Owner.User.get('name'),
                             TestVApp._empty_vapp_owner_name)
        finally:
            org_admin_client.logout()

    def test_0100_vapp_metadata(self):
        """Test the methods related to metadata manipulation in vapp.py.

        This test passes if all the metadata operations are successful.
        """
        logger = Environment.get_default_logger()
        vapp_name = TestVApp._empty_vapp_name
        vapp = Environment.get_vapp_in_test_vdc(
            client=TestVApp._client, vapp_name=vapp_name)

        # add new metadata
        logger.debug(f'Adding metadata [key={TestVApp._metadata_key},'
                     'value={TestVApp._metadata_value}]) to vApp:'
                     '{vapp_name}')
        task = vapp.set_metadata(
            domain=MetadataDomain.GENERAL.value,
            visibility=MetadataVisibility.READ_WRITE,
            key=TestVApp._metadata_key,
            value=TestVApp._metadata_value)
        result = TestVApp._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

        # retrieve metadata
        logger.debug(f'Retriving metadata with key='
                     '{TestVApp._metadata_key} from vApp:{vapp_name}.')
        entries = metadata_to_dict(vapp.get_metadata())
        self.assertTrue(
            TestVApp._metadata_key in entries, f'Should have '
            'been able to retrieve metadata entry with '
            'key={TestVApp._metadata_key}.')

        # update metadata value as org admin
        logger.debug(f'Updtaing metadata on vApp:{vapp_name} with key='
                     '{TestVApp._metadata_key} to value='
                     '{TestVApp._metadata_new_value}.')
        task = vapp.set_metadata(
            domain=MetadataDomain.GENERAL.value,
            visibility=MetadataVisibility.READ_WRITE,
            key=TestVApp._metadata_key,
            value=TestVApp._metadata_new_value)
        TestVApp._client.get_task_monitor().wait_for_success(task)
        entries = metadata_to_dict(vapp.get_metadata())
        self.assertEqual(TestVApp._metadata_new_value,
                         entries[TestVApp._metadata_key])

        # remove metadata entry
        logger.debug(f'Removing metadata with '
                     'key={TestVApp._metadata_key} from vApp:{vapp_name}.')
        task = vapp.remove_metadata(key=TestVApp._metadata_key)
        result = TestVApp._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0110_create_vapp_network(self):
        """Test the method vapp.create_vapp_network().

        This test passes if the vApp network creation is successful.
        """
        logger = Environment.get_default_logger()
        vapp_name = TestVApp._customized_vapp_name
        vapp = Environment.get_vapp_in_test_vdc(
            client=TestVApp._client, vapp_name=vapp_name)
        logger.debug('Creating a vApp network in ' +
                     TestVApp._customized_vapp_name)
        task = vapp.create_vapp_network(
            TestVApp._vapp_network_name, TestVApp._vapp_network_cidr,
            TestVApp._vapp_network_description, TestVApp._vapp_network_dns1,
            TestVApp._vapp_network_dns2, TestVApp._vapp_network_dns_suffix,
            [TestVApp._vapp_network_ip_range])
        result = TestVApp._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        # Verification
        vapp.reload()
        self.assertTrue(
            self._is_network_present(vapp.get_resource(),
                                     TestVApp._vapp_network_name))

    def _is_network_present(vapp, network_name):
        for network_config in vapp.NetworkConfigSection.NetworkConfig:
            if (network_config.get('networkName') == network_name):
                return True
        return False

    def test_0120_reset_vapp_network(self):
        """Test the method vapp.reset_vapp_network().

        This test passes if reset network is successful.
        """
        vapp = Environment.get_vapp_in_test_vdc(
            client=TestVApp._client, vapp_name=TestVApp._customized_vapp_name)

        # make sure the vApp is powered on before resetting
        task = vapp.undeploy()
        TestVApp._client.get_task_monitor().wait_for_success(task=task)
        vapp.reload()
        task = vapp.deploy(power_on=True)
        TestVApp._client.get_task_monitor().wait_for_success(task=task)
        vapp.reload()
        self.assertTrue(vapp.is_powered_on())

        task = vapp.reset_vapp_network(TestVApp._vapp_network_name)
        TestVApp._client.get_task_monitor().wait_for_success(task=task)
        vapp.reload()

    def test_0130_delete_vapp_network(self):
        """Test the method vapp.delete_vapp_network().

        This test passes if delete network is successful.
        """
        vapp = Environment.get_vapp_in_test_vdc(
            client=TestVApp._client, vapp_name=TestVApp._customized_vapp_name)

        task = vapp.delete_vapp_network(TestVApp._vapp_network_name)
        TestVApp._client.get_task_monitor().wait_for_success(task=task)

        # Verification
        vapp.reload()
        self.assertFalse(
            self._is_network_present(vapp.get_resource(),
                                     TestVApp._vapp_network_name))

    @developerModeAware
    def test_9998_teardown(self):
        """Test the  method vdc.delete_vapp().

        Invoke the method for all the vApps created by setup.

        This test passes if all the tasks for deleting the vApps succeed.
        """
        vapps_to_delete = []
        if TestVApp._empty_vapp_href is not None:
            vapps_to_delete.append(TestVApp._empty_vapp_name)
        if TestVApp._customized_vapp_href is not None:
            vapps_to_delete.append(TestVApp._customized_vapp_name)

        vdc = Environment.get_test_vdc(TestVApp._client)

        for vapp_name in vapps_to_delete:
            task = vdc.delete_vapp(name=vapp_name, force=True)
            result = TestVApp._client.get_task_monitor().wait_for_success(task)
            self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_9999_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestVApp._client.logout()


if __name__ == '__main__':
    unittest.main()
