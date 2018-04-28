import random
import string
import unittest

from pyvcloud.vcd.client import NetworkAdapterType
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import TaskStatus
from pyvcloud.vcd.vapp import VApp
from pyvcloud.system_test_framework.base_test import BaseTestCase
from pyvcloud.system_test_framework.environment import CommonRoles
from pyvcloud.system_test_framework.environment import developerModeAware
from pyvcloud.system_test_framework.environment import Environment


class TestVApp(BaseTestCase):
    """Test vApp functionalities implemented in pyvcloud."""
    _client = None

    _empty_vapp_name = 'empty_vApp'
    _empty_vapp_description = 'empty vApp description'
    _empty_vapp_href = None

    _customized_vapp_name = 'customized_vApp'
    _customized_vapp_description = 'customized vApp description'
    _customized_vapp_memory_size = 64   # MB
    _customized_vapp_num_cpu = 2
    _customized_vapp_disk_size = 100   # MB
    _customized_vapp_vm_name = 'custom-vm'
    _customized_vapp_vm_hostname = 'custom-host'
    _customized_vapp_vm_network_adapter_type = NetworkAdapterType.VMXNET3
    _customized_vapp_href = None

    _non_existent_vapp_name = 'non_existent_vapp_'\
                              .join(random.choices(string.ascii_letters, k=8))

    def test_0000_setup(self):
        """
        """
        TestVApp._client = Environment.get_client_in_default_org(
            CommonRoles.CATALOG_AUTHOR)
        vdc = Environment.get_test_vdc(TestVApp._client)

        try:
            vapp_resource = vdc.get_vapp(TestVApp._empty_vapp_name)
            print('Reusing empty vApp')
            TestVApp._empty_vapp_href = vapp_resource.get('href')
        except Exception as e:
            if 'not found' in str(e):
                TestVApp._empty_vapp_href = self._create_empty_vapp(
                    TestVApp._client,
                    vdc)
            else:
                raise e

        try:
            vapp_resource = vdc.get_vapp(TestVApp._customized_vapp_name)
            print('Reusing cusomized vApp')
            TestVApp._customized_vapp_href = vapp_resource.get('href')
        except Exception as e:
            if 'not found' in str(e):
                TestVApp._customized_vapp_href = \
                    self._create_customized_vapp_from_template(
                        TestVApp._client,
                        vdc)
            else:
                raise e

    def _create_empty_vapp(self, client, vdc):
        """
        """
        print('Creating empty vApp.')
        vapp_sparse_resouce = vdc.create_vapp(
            name=TestVApp._empty_vapp_name,
            description=TestVApp._empty_vapp_description,
            accept_all_eulas=True)

        task = client.get_task_monitor().wait_for_success(
            vapp_sparse_resouce.Tasks.Task[0])
        self.assertEqual(task.get('status'), TaskStatus.SUCCESS.value)

        return vapp_sparse_resouce.get('href')

    def _create_customized_vapp_from_template(self, client, vdc):
        """
        """
        print('Creating customized vApp.')
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
            network_adapter_type=TestVApp
                                 ._customized_vapp_vm_network_adapter_type)

        task = client.get_task_monitor().wait_for_success(
            vapp_sparse_resouce.Tasks.Task[0])
        self.assertEqual(task.get('status'), TaskStatus.SUCCESS.value)

        return vapp_sparse_resouce.get('href')

    def test_0010_get_vapp(self):
        """
        """
        vdc = Environment.get_test_vdc(TestVApp._client)
        vapp_resource = vdc.get_vapp(TestVApp._customized_vapp_name)
        self.assertIsNotNone(vapp_resource)

    def test_0020_get_nonexistent_vapp(self):
        """
        """
        vdc = Environment.get_test_vdc(TestVApp._client)
        try:
            vdc.get_vapp(TestVApp._non_existent_vapp_name)
            self.fail('Should not be able to fetch vApp ' +
                      TestVApp._non_existent_vapp_name)
        except Exception as e:
            self.assertTrue('not found' in str(e))

    def test_0020_add_vm(self):
        pass

    def test_0030_customized_vapp(self):
        vdc = Environment.get_test_vdc(TestVApp._client)
        vapp_resource = vdc.get_vapp(TestVApp._customized_vapp_name)
        vms = vapp_resource.xpath(
            '//vcloud:VApp/vcloud:Children/vcloud:Vm', namespaces=NSMAP)
        self.assertTrue(len(vms) >= 1)

        items = vms[0].xpath('//ovf:VirtualHardwareSection/ovf:Item',
                             namespaces={'ovf': NSMAP['ovf']})
        self.assertTrue(len(items) > 0)

        found_disk = False
        for item in items:
            if item['{' + NSMAP['rasd'] + '}ResourceType'] == 17:
                found_disk = True
                assert item['{' + NSMAP['rasd'] + '}VirtualQuantity'] == \
                    (TestVApp._customized_vapp_disk_size * 1024 * 1024)
                break

        # this check makes sure that the vm isn't disk-less
        assert found_disk

    def _power_on_vapp_if_possible(self, client, vapp):
        # TODO : update power_on to handle missing link exception
        # see VCDA-603
        try:
            print('Making sure vApp ' + vapp.get_resource().get('name') +
                  ' is powered on.')
            task = vapp.power_on()
            client.get_task_monitor().wait_for_success(task=task)
        except Exception as e:
            pass

    def test_0040_vapp_power_options(self):
        """
        """
        vdc = Environment.get_test_vdc(TestVApp._client)
        vapp_name = TestVApp._customized_vapp_name
        vapp_resource = vdc.get_vapp(vapp_name)
        vapp = VApp(TestVApp._client, resource=vapp_resource)

        # make sure the vApp is powered on before running tests
        self._power_on_vapp_if_possible(TestVApp._client, vapp)

        print('Undeploying vApp ' + vapp_name)
        task = vapp.undeploy()
        result = TestVApp._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

        print('Deploying vApp ' + vapp_name)
        vapp.reload()
        task = vapp.deploy(power_on=False)
        result = TestVApp._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

        print('Powering on vApp ' + vapp_name)
        vapp.reload()
        task = vapp.power_on()
        result = TestVApp._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

        print('Reseting (power) vApp ' + vapp_name)
        vapp.reload()
        task = vapp.power_reset()
        result = TestVApp._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

        print('Powering off vApp ' + vapp_name)
        vapp.reload()
        task = vapp.power_off()
        result = TestVApp._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

        print('Powering back on vApp ' + vapp_name)
        vapp.reload()
        task = vapp.power_on()
        result = TestVApp._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

        print('Rebooting (power) vApp ' + vapp_name)
        vapp.reload()
        task = vapp.reboot()
        result = TestVApp._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)

        print('Shutting down vApp ' + vapp_name)
        vapp.reload()
        task = vapp.shutdown()
        result = TestVApp._client.get_task_monitor().wait_for_success(task)
        self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        # end state of vApp is deployed and powered off.

    def test_0050_vapp_network_connection(self):
        try:
            client = Environment.get_client_in_default_org(
                CommonRoles.ORGANIZATION_ADMINISTRATOR)

            network_name = Environment.get_default_orgvdc_network_name()

            vdc = Environment.get_test_vdc(client)
            vapp_name = TestVApp._customized_vapp_name
            vapp_resource = vdc.get_vapp(vapp_name)
            vapp = VApp(client, resource=vapp_resource)

            print('Connecting vApp ' + vapp_name + ' to orgvdc network ' +
                  network_name)
            task = vapp.connect_org_vdc_network(network_name)
            result = client.get_task_monitor().wait_for_success(task)
            self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
            
            print('Dis-connecting vApp ' + vapp_name + ' to orgvdc network ' +
                  network_name)
            task = vapp.disconnect_org_vdc_network(network_name)
            result = client.get_task_monitor().wait_for_success(task)
            self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        finally:
            client.logout()

    def test_0060_vapp_acl(self):
        # test acl - add, get, remove, remove all, share, unshare
        pass

    def test_0070_vapp_lease(self):
        pass

    def test_0080_change_vapp_owner(self):
        pass

    @developerModeAware
    def test_9999_teardown(self):
        vapps_to_delete = []
        if TestVApp._empty_vapp_href is not None:
            vapps_to_delete.append(TestVApp._empty_vapp_name)
        if TestVApp._customized_vapp_href is not None:
            vapps_to_delete.append(TestVApp._customized_vapp_name)

        vdc = Environment.get_test_vdc(TestVApp._client)
        try:
            for vapp_name in vapps_to_delete:
                task = vdc.delete_vapp(name=vapp_name, force=True)
                result = TestVApp._client.get_task_monitor().wait_for_success(
                    task)
                self.assertEqual(result.get('status'),
                                 TaskStatus.SUCCESS.value)
        finally:
            TestVApp._client.logout()


if __name__ == '__main__':
    unittest.main()
