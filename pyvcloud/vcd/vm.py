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

from pyvcloud.vcd.client import E
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import RelationType


class VM(object):
    """A helper class to work with Virtual Machines."""

    def __init__(self, client, href=None, resource=None):
        """Constructor.

        :param client: (Client): The client object to communicate with vCD.
        :param href: (str): (optional) href of the VM.
        :param resource: (:class:`lxml.objectify.StringElement`): (optional)
            object describing the VM.
        """
        self.client = client
        if href is None and resource is None:
            raise TypeError("VM initialization failed as arguments "
                            "are either invalid or None")
        self.href = href
        self.resource = resource
        if resource is not None:
            self.href = resource.get('href')

    def reload(self):
        """Updates the xml representation of the VM from vCD."""
        self.resource = self.client.get_resource(self.href)
        if self.resource is not None:
            self.href = self.resource.get('href')

    def modify_cpu(self, virtual_quantity, cores_per_socket=None):
        """Updates the number of CPUs of a VM.

        :param virtual_quantity: (int): The number of virtual CPUs to configure
            on the VM.
        :param cores_per_socket: (int): The number of cores per socket.

        :return:  A :class:`lxml.objectify.StringElement` object describing the
            asynchronous task that updates the VM.
        """
        uri = self.href + '/virtualHardwareSection/cpu'
        if cores_per_socket is None:
            cores_per_socket = virtual_quantity
        item = self.client.get_resource(uri)
        item['{' + NSMAP['rasd'] +
             '}ElementName'] = '%s virtual CPU(s)' % virtual_quantity
        item['{' + NSMAP['rasd'] + '}VirtualQuantity'] = virtual_quantity
        item['{' + NSMAP['vmw'] + '}CoresPerSocket'] = cores_per_socket
        return self.client.put_resource(uri, item, EntityType.RASD_ITEM.value)

    def modify_memory(self, virtual_quantity):
        """Updates the memory of a VM.

        :param virtual_quantity: (int): The number of MB of memory to configure
            on the VM.

        :return:  A :class:`lxml.objectify.StringElement` object describing the
            asynchronous task that updates the VM.
        """
        uri = self.href + '/virtualHardwareSection/memory'
        item = self.client.get_resource(uri)
        item['{' + NSMAP['rasd'] +
             '}ElementName'] = '%s virtual CPU(s)' % virtual_quantity
        item['{' + NSMAP['rasd'] + '}VirtualQuantity'] = virtual_quantity
        return self.client.put_resource(uri, item, EntityType.RASD_ITEM.value)

    def shutdown(self):
        """Shutdown the VM.

        :return: A :class:`lxml.objectify.StringElement` object describing
            the asynchronous Task shutting down the VM.
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        return self.client.post_linked_resource(
            self.resource, RelationType.POWER_SHUTDOWN, None, None)

    def reboot(self):
        """Reboots the VM.

        :return: A :class:`lxml.objectify.StringElement` object describing
            the asynchronous Task rebooting the VM.
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        return self.client.post_linked_resource(
            self.resource, RelationType.POWER_REBOOT, None, None)

    def power_on(self):
        """Powers on the VM.

        :return:  A :class:`lxml.objectify.StringElement` object describing the
            asynchronous task that operates on the VM.
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        return self.client.post_linked_resource(
            self.resource, RelationType.POWER_ON, None, None)

    def power_off(self):
        """Powers off the VM.

        :return:  A :class:`lxml.objectify.StringElement` object describing the
            asynchronous task that operates on the VM.
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        return self.client.post_linked_resource(
            self.resource, RelationType.POWER_OFF, None, None)

    def power_reset(self):
        """Powers reset the VM.

        :return:  A :class:`lxml.objectify.StringElement` object describing the
            asynchronous task that operates on the VM.
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        return self.client.post_linked_resource(
            self.resource, RelationType.POWER_RESET, None, None)

    def deploy(self, power_on=True, force_customization=False):
        """Deploys the VM.

        Deploying the VM will allocate all resources assigned
        to the VM. If an already deployed VM is attempted to deploy,
        an exception is raised.

        :return:  A :class:`lxml.objectify.StringElement` object describing the
            asynchronous task that operates on the VM.
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        deploy_vm_params = E.DeployVAppParams()
        deploy_vm_params.set('powerOn', str(power_on).lower())
        deploy_vm_params.set('forceCustomization',
                             str(force_customization).lower())
        return self.client.post_linked_resource(
            self.resource, RelationType.DEPLOY, EntityType.DEPLOY.value,
            deploy_vm_params)

    def undeploy(self, action='default'):
        """Undeploy the VM.

        :return:  A :class:`lxml.objectify.StringElement` object describing the
            asynchronous task that operates on the VM.
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        params = E.UndeployVAppParams(E.UndeployPowerAction(action))
        return self.client.post_linked_resource(
            self.resource, RelationType.UNDEPLOY, EntityType.UNDEPLOY.value,
            params)

    def get_cpus(self):
        """Returns the number of CPUs.

        :return: A dictionary with:
            num_cpus: (int): number of cpus
            num_cores_per_socket: (int): number of cores per socket
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        return {
            'num_cpus':
            int(self.resource.VmSpecSection.NumCpus.text),
            'num_cores_per_socket':
            int(self.resource.VmSpecSection.NumCoresPerSocket.text)
        }

    def get_memory(self):
        """Returns the amount of memory in MB.

        :return: (int): Amount of memory in MB
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        return int(
            self.resource.VmSpecSection.MemoryResourceMb.Configured.text)

    def get_vc(self):
        """Returns the vCenter where this VM is located.

        :return: (str): Name of the vCenter
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        for record in self.resource.VCloudExtension[
                '{' + NSMAP['vmext'] + '}VmVimInfo'].iterchildren():
            if hasattr(record, '{' + NSMAP['vmext'] + '}VimObjectType'):
                if 'VIRTUAL_MACHINE' == record.VimObjectType.text:
                    return record.VimServerRef.get('name')
        return None
