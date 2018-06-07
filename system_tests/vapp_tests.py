import unittest
from uuid import uuid1

from pyvcloud.system_test_framework.base_test import BaseTestCase
from pyvcloud.system_test_framework.environment import CommonRoles
from pyvcloud.system_test_framework.environment import developerModeAware
from pyvcloud.system_test_framework.environment import Environment

from pyvcloud.vcd.client import NetworkAdapterType
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import TaskStatus
from pyvcloud.vcd.exceptions import EntityNotFoundException


class TestVApp(BaseTestCase):
    """Test vApp functionalities implemented in pyvcloud."""

    # TODO(VCDA-603) - Once the share catalog bug is fixed, the runner should
    # be changed to vApp Author
    _test_runner_role = CommonRoles.CATALOG_AUTHOR
    _client = None

    _empty_vapp_name = 'empty_vApp'
    _empty_vapp_description = 'empty vApp description'
    _empty_vapp_runtime_lease = 86400  # in seconds
    _empty_vapp_storage_lease = 86400  # in seconds
    _empty_vapp_owner_name = None
    _empty_vapp_href = None

    _additional_vm_name = 'additional-vm'

    _customized_vapp_name = 'customized_vApp'
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

    def test_0000_setup(self):
        """Setup the vApps required for the other tests in this module.

        Create two vApps as per the configuration stated above. In case the
           vApps exist, re-use them.

        This test passes if the two vApp hrefs are not None.
        """
        logger = Environment.get_default_logger()
        TestVApp._client = Environment.get_client_in_default_org(
            TestVApp._test_runner_role)
        vdc = Environment.get_test_vdc(TestVApp._client)

        try:
            vapp_resource = vdc.get_vapp(TestVApp._empty_vapp_name)
            logger.debug('Reusing empty vApp')
            TestVApp._empty_vapp_href = vapp_resource.get('href')
            TestVApp._empty_vapp_owner_name = \
                vapp_resource.Owner.User.get('name')
        except EntityNotFoundException as e:
            TestVApp._empty_vapp_href = self._create_empty_vapp(
                TestVApp._client, vdc)
            TestVApp._empty_vapp_owner_name = Environment.\
                get_username_for_role_in_test_org(TestVApp._test_runner_role)

        try:
            vapp_resource = vdc.get_vapp(TestVApp._customized_vapp_name)
            logger.debug('Reusing customized vApp')
            TestVApp._customized_vapp_href = vapp_resource.get('href')
            TestVApp._customized_vapp_owner_name = \
                vapp_resource.Owner.User.get('name')
        except EntityNotFoundException as e:
            TestVApp._customized_vapp_href = \
                self._create_customized_vapp_from_template(
                    TestVApp._client,
                    vdc)
            TestVApp._customized_vapp_owner_name = Environment.\
                get_username_for_role_in_test_org(
                    TestVApp._test_runner_role)

        self.assertIsNotNone(TestVApp._empty_vapp_href)
        self.assertIsNotNone(TestVApp._customized_vapp_href)

    def _create_empty_vapp(self, client, vdc):
        """Helper method to create an empty vApp.

        :param client: An object of :class: `pyvcloud.vcd.client.Client` that
            would be used to make ReST calls to vCD.
        :param vdc: An object of :class:`lxml.objectify.StringElement`
            describing the vdc in which the vApp will be created.

        :return: (str): href of the created vApp
        """
        logger = Environment.get_default_logger()
        logger.debug('Creating empty vApp.')
        vapp_sparse_resouce = vdc.create_vapp(
            name=TestVApp._empty_vapp_name,
            description=TestVApp._empty_vapp_description,
            accept_all_eulas=True)

        task = client.get_task_monitor().wait_for_success(
            vapp_sparse_resouce.Tasks.Task[0])
        self.assertEqual(task.get('status'), TaskStatus.SUCCESS.value)

        return vapp_sparse_resouce.get('href')

    def _create_customized_vapp_from_template(self, client, vdc):
        """Helper method to create a customized vApp from template.

        :param client: An object of :class: `pyvcloud.vcd.client.Client` that
            would be used to make ReST calls to vCD.
        :param vdc: An object of :class:`lxml.objectify.StringElement`
            describing the vdc in which the vApp will be created.

        :return: (str): href of the created vApp
        """
        logger = Environment.get_default_logger()
        logger.debug('Creating customized vApp.')
        vapp_sparse_resouce = vdc.instantiate_vapp(
            name=TestVApp._customized_vapp_name,
            catalog=Environment.get_default_catalog_name(),
            template=Environment.get_default_template_name(),
            deploy=True,
            power_on=True,
            accept_all_eulas=True,
            memory=TestVApp._customized_vapp_memory_size,
            cpu=TestVApp._customized_vapp_num_cpu,
            disk_size=TestVApp._customized_vapp_disk_size,
            vm_name=TestVApp._customized_vapp_vm_name,
            hostname=TestVApp._customized_vapp_vm_hostname,
            network_adapter_type=TestVApp.
            _customized_vapp_vm_network_adapter_type)

        task = client.get_task_monitor().wait_for_success(
            vapp_sparse_resouce.Tasks.Task[0])
        self.assertEqual(task.get('status'), TaskStatus.SUCCESS.value)

        return vapp_sparse_resouce.get('href')

    def test_0010_get_vapp(self):
        """Test the method vdc.get_vapp().

        This test passes if the expected vApp can be successfully retrieved
           by name.
        """
        vdc = Environment.get_test_vdc(TestVApp._client)
        vapp_resource = vdc.get_vapp(TestVApp._customized_vapp_name)
        self.assertIsNotNone(vapp_resource)

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
        self.fail('Should fail with EntityNotFoundException while fetching'
                  'vApp ' + TestVApp._non_existent_vapp_name)

    def test_0020_add_delete_vm(self):
        """Test the method vapp.add_vms() and vapp.delete_vms().

        This test passes if the supplied vm is sucessfully added to the vApp
           and then successfully removed from the vApp.
        """
        logger = Environment.get_default_logger()
        vapp_name = TestVApp._empty_vapp_name
        vapp = Environment.get_vapp_in_test_vdc(
            client=TestVApp._client, vapp_name=vapp_name)

        source_vapp_resource = Environment.get_default_vapp(TestVApp._client).\
            get_resource()
        source_vm_name = Environment.get_default_vm_name()
        target_vm_name = TestVApp._additional_vm_name
        spec = {
            'vapp': source_vapp_resource,
            'source_vm_name': source_vm_name,
            'target_vm_name': target_vm_name
        }

        logger.debug('Adding vm ' + target_vm_name + ' to vApp ' + vapp_name)
        # deploy and power_on are false to make sure that the subsequent
        # deletion of vm doesn't require additional power operations
        task = vapp.add_vms(
            [spec], deploy=False, power_on=False, all_eulas_accepted=True)
        result = TestVApp._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

        logger.debug(
            'Removing vm ' + target_vm_name + ' from vApp ' + vapp_name)
        vapp.reload()
        task = vapp.delete_vms([target_vm_name])
        result = TestVApp._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

    def test_0030_customized_vapp(self):
        """Test the correctness of the customization of vdc.instantiate_vapp().

        This test passes if the customized vApp is retrieved successfully
           and it's verified that the vApp is correctly customized as per the
           config in this file.
        """
        vapp_name = TestVApp._customized_vapp_name
        vapp = Environment.get_vapp_in_test_vdc(
            client=TestVApp._client, vapp_name=vapp_name)
        vapp_resource = vapp.get_resource()

        # TODO(https://github.com/vmware/vcd-cli/issues/220) : Bug in
        # vdc.vapp_instantiate() doesn't take description as parameter.

        # self.assertEqual(vapp_resource.Description.text,
        #                 TestVApp._customized_vapp_description)

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

    def _power_on_vapp_if_possible(self, client, vapp):
        """Power on a vApp if possible, else fail silently.

        :param client: An object of :class: `pyvcloud.vcd.client.Client` that
            would be used to make ReST calls to vCD.
        :param vapp: An object of :class:`lxml.objectify.StringElement`
            describing the vapp which we want to power on.

        :return: Nothing
        """
        # TODO(VCDA-603) : update power_on to handle missing link exception
        try:
            logger = Environment.get_default_logger()
            logger.debug('Making sure vApp ' +
                         vapp.get_resource().get('name') + ' is powered on.')
            task = vapp.power_on()
            client.get_task_monitor().wait_for_success(task=task)
        except Exception as e:
            pass

    def test_0040_vapp_power_options(self):
        """Test the method related to power operations in vapp.py.

        This test passes if all the power operations are successful.
        """
        logger = Environment.get_default_logger()
        vapp_name = TestVApp._customized_vapp_name
        vapp = Environment.get_vapp_in_test_vdc(
            client=TestVApp._client, vapp_name=vapp_name)

        # make sure the vApp is powered on before running tests
        self._power_on_vapp_if_possible(TestVApp._client, vapp)

        logger.debug('Un-deploying vApp ' + vapp_name)
        vapp.reload()
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

    def test_0050_vapp_network_connection(self):
        """Test vapp.connect/disconnect_org_vdc_network().

        This test passes if the connect and disconnect to orgvdc network
           operations are successful.
        """
        try:
            logger = Environment.get_default_logger()
            client = Environment.get_client_in_default_org(
                CommonRoles.ORGANIZATION_ADMINISTRATOR)

            network_name = Environment.get_default_orgvdc_network_name()

            vapp_name = TestVApp._customized_vapp_name
            vapp = Environment.get_vapp_in_test_vdc(
                client=client, vapp_name=vapp_name)

            logger.debug('Connecting vApp ' + vapp_name +
                         ' to orgvdc network ' + network_name)
            task = vapp.connect_org_vdc_network(network_name)
            result = client.get_task_monitor().wait_for_success(task)
            self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

            logger.debug('Disconnecting vApp ' + vapp_name +
                         ' to orgvdc network ' + network_name)
            vapp.reload()
            task = vapp.disconnect_org_vdc_network(network_name)
            result = client.get_task_monitor().wait_for_success(task)
            self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        finally:
            client.logout()

    def test_0060_vapp_acl(self):
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
        control_access = vapp.add_access_settings(
            access_settings_list=[{
                'name': console_user_name,
                'type': 'user'
            }, {
                'name': vapp_user_name,
                'type': 'user',
                'access_level': 'Change'
            }])
        self.assertEqual(len(control_access.AccessSettings.AccessSetting), 2)

        # get
        logger.debug('Fetching access control rules for vApp ' + vapp_name)
        vapp.reload()
        control_access = vapp.get_access_settings()
        self.assertEqual(len(control_access.AccessSettings.AccessSetting), 2)

        # remove
        logger.debug('Fetching access control rules for vApp ' + vapp_name)
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
        logger.debug(
            'Un-sharing vApp ' + vapp_name + ' from everyone in the org')
        vapp.reload()
        control_access = vapp.unshare_from_org_members()
        self.assertEqual(control_access.IsSharedToEveryone.text, 'false')

        # remove all access control rules again
        logger.debug('Removing all access control from vApp ' + vapp_name)
        control_access = vapp.remove_access_settings(remove_all=True)
        self.assertFalse(hasattr(control_access, 'AccessSettings'))

    def test_0070_vapp_lease(self):
        """Test the method vapp.set_lease().

        This test passes if the lease setting operation completes
           successfully.
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

    def test_0080_change_vapp_owner(self):
        """Test the method vapp.change_owner().

        This test passes if the owner of the vApp is successfuly changed
           to the desired user.
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

    @unittest.skip("Not enough documentation")
    def test_0090_vapp_metadata(self):
        """Test vapp.set/get_metadata()."""
        # TODO() - Unclear about the use of this feature, not enough
        # documentation in vapp.py
        pass

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
