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

from pyvcloud.vcd.client import E
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.exceptions import InvalidParameterException


class VM(object):
    """A helper class to work with Virtual Machines."""

    def __init__(self, client, href=None, resource=None):
        """Constructor for VM object.

        :param pyvcloud.vcd.client.Client client: the client that will be used
            to make REST calls to vCD.
        :param str href: href of the vm.
        :param lxml.objectify.ObjectifiedElement resource: object containing
            EntityType.VM XML data representing the vm.
        """
        self.client = client
        if href is None and resource is None:
            raise InvalidParameterException(
                "VM initialization failed as arguments "
                "are either invalid or None")
        self.href = href
        self.resource = resource
        if resource is not None:
            self.href = resource.get('href')

    def reload(self):
        """Reloads the resource representation of the vm.

        This method should be called in between two method invocations on the
        VM object, if the former call changes the representation of the
        vm in vCD.
        """
        self.resource = self.client.get_resource(self.href)
        if self.resource is not None:
            self.href = self.resource.get('href')

    def modify_cpu(self, virtual_quantity, cores_per_socket=None):
        """Updates the number of CPUs of a vm.

        :param int virtual_quantity: number of virtual CPUs to configure on the
            vm.
        :param int cores_per_socket: number of cores per socket.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that updates the vm.

        :rtype: lxml.objectify.ObjectifiedElement
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
        """Updates the memory of a vm.

        :param int virtual_quantity: number of MB of memory to configure on the
            vm.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that updates the vm.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        uri = self.href + '/virtualHardwareSection/memory'
        item = self.client.get_resource(uri)
        item['{' + NSMAP['rasd'] +
             '}ElementName'] = '%s virtual CPU(s)' % virtual_quantity
        item['{' + NSMAP['rasd'] + '}VirtualQuantity'] = virtual_quantity
        return self.client.put_resource(uri, item, EntityType.RASD_ITEM.value)

    def shutdown(self):
        """Shutdown the vm.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task shutting down the vm.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        return self.client.post_linked_resource(
            self.resource, RelationType.POWER_SHUTDOWN, None, None)

    def reboot(self):
        """Reboots the vm.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task rebooting the vm.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        return self.client.post_linked_resource(
            self.resource, RelationType.POWER_REBOOT, None, None)

    def power_on(self):
        """Powers on the vm.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is powering on the vm.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        return self.client.post_linked_resource(
            self.resource, RelationType.POWER_ON, None, None)

    def power_off(self):
        """Powers off the vm.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is powering off the vm.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        return self.client.post_linked_resource(
            self.resource, RelationType.POWER_OFF, None, None)

    def power_reset(self):
        """Powers reset the vm.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is power resetting the vm.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        return self.client.post_linked_resource(
            self.resource, RelationType.POWER_RESET, None, None)

    def snapshot_create(self, memory=None, quiesce=None, name=None):
        """Create a snapshot of the vm.

        :param bool memory: True, if the snapshot should include the virtual
            machine's memory.
        :param bool quiesce: True, if the file system of the virtual machine
            should be quiesced before the snapshot is created. Requires VMware
            tools to be installed on the vm.
        :param str name: name of the snapshot.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is creating the snapshot.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        snapshot_vm_params = E.CreateSnapshotParams()
        if memory is not None:
            snapshot_vm_params.set('memory', str(memory).lower())
        if quiesce is not None:
            snapshot_vm_params.set('quiesce', str(quiesce).lower())
        if name is not None:
            snapshot_vm_params.set('name', str(name).lower())
        return self.client.post_linked_resource(
            self.resource, RelationType.SNAPSHOT_CREATE,
            EntityType.SNAPSHOT_CREATE.value, snapshot_vm_params)

    def snapshot_revert_to_current(self):
        """Reverts a virtual machine to the current snapshot, if any.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is reverting the snapshot.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        return self.client.post_linked_resource(
            self.resource, RelationType.SNAPSHOT_REVERT_TO_CURRENT, None, None)

    def snapshot_remove_all(self):
        """Removes all user created snapshots of a virtual machine.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task removing the snapshots.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        return self.client.post_linked_resource(
            self.resource, RelationType.SNAPSHOT_REMOVE_ALL, None, None)

    def deploy(self, power_on=True, force_customization=False):
        """Deploys the vm.

        Deploying the vm will allocate all resources assigned to the vm. If an
        attempt is made to deploy an already deployed vm, an exception will be
        raised.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is deploying the vm.

        :rtype: lxml.objectify.ObjectifiedElement
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
        """Undeploy the vm.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is undeploying the vm.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        params = E.UndeployVAppParams(E.UndeployPowerAction(action))
        return self.client.post_linked_resource(
            self.resource, RelationType.UNDEPLOY, EntityType.UNDEPLOY.value,
            params)

    def get_cpus(self):
        """Returns the number of CPUs in the vm.

        :return: number of cpus (int) and number of cores per socket (int) of
            the vm.

        :rtype: dict
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

        :return: amount of memory in MB.

        :rtype: int
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        return int(
            self.resource.VmSpecSection.MemoryResourceMb.Configured.text)

    def get_vc(self):
        """Returns the vCenter where this vm is located.

        :return: name of the vCenter server.

        :rtype: str
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        for record in self.resource.VCloudExtension[
                '{' + NSMAP['vmext'] + '}VmVimInfo'].iterchildren():
            if hasattr(record, '{' + NSMAP['vmext'] + '}VimObjectType'):
                if 'VIRTUAL_MACHINE' == record.VimObjectType.text:
                    return record.VimServerRef.get('name')
        return None
