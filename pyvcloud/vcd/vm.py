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
from pyvcloud.vcd.client import IpAddressMode
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.client import VCLOUD_STATUS_MAP
from pyvcloud.vcd.client import VmNicProperties
from pyvcloud.vcd.exceptions import InvalidParameterException
from pyvcloud.vcd.exceptions import OperationNotSupportedException


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
                'VM initialization failed as arguments are either invalid or'
                ' None')
        self.href = href
        self.resource = resource
        if resource is not None:
            self.href = resource.get('href')

    def get_resource(self):
        """Fetches the XML representation of the vm from vCD.

        Will serve cached response if possible.

        :return: object containing EntityType.VM XML data representing the vm.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.reload()
        return self.resource

    def reload(self):
        """Reloads the resource representation of the vm.

        This method should be called in between two method invocations on the
        VM object, if the former call changes the representation of the
        vm in vCD.
        """
        self.resource = self.client.get_resource(self.href)
        if self.resource is not None:
            self.href = self.resource.get('href')

    def get_vc(self):
        """Returns the vCenter where this vm is located.

        :return: name of the vCenter server.

        :rtype: str
        """
        self.get_resource()
        for record in self.resource.VCloudExtension[
                '{' + NSMAP['vmext'] + '}VmVimInfo'].iterchildren():
            if hasattr(record, '{' + NSMAP['vmext'] + '}VimObjectType'):
                if 'VIRTUAL_MACHINE' == record.VimObjectType.text:
                    return record.VimServerRef.get('name')
        return None

    def get_cpus(self):
        """Returns the number of CPUs in the vm.

        :return: number of cpus (int) and number of cores per socket (int) of
            the vm.

        :rtype: dict
        """
        self.get_resource()
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
        self.get_resource()
        return int(
            self.resource.VmSpecSection.MemoryResourceMb.Configured.text)

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
        item['{' + NSMAP['rasd'] + '}ElementName'] = \
            '%s virtual CPU(s)' % virtual_quantity
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
        item['{' + NSMAP['rasd'] + '}ElementName'] = \
            '%s virtual CPU(s)' % virtual_quantity
        item['{' + NSMAP['rasd'] + '}VirtualQuantity'] = virtual_quantity
        return self.client.put_resource(uri, item, EntityType.RASD_ITEM.value)

    def get_power_state(self, vm_resource=None):
        """Returns the status of the vm.

        :param lxml.objectify.ObjectifiedElement vm_resource: object
            containing EntityType.VM XML data representing the vm whose
            power state we want to retrieve.

        :return: The status of the vm, the semantics of the value returned is
            captured in pyvcloud.vcd.client.VCLOUD_STATUS_MAP

        :rtype: int
        """
        if vm_resource is None:
            vm_resource = self.get_resource()
        return int(vm_resource.get('status'))

    def is_powered_on(self, vm_resource=None):
        """Checks if a vm is powered on or not.

        :param lxml.objectify.ObjectifiedElement vm_resource: object
            containing EntityType.VM XML data representing the vm whose
            power state we want to check.

        :return: True if the vm is powered on else False.

        :rtype: bool
        """
        return self.get_power_state(vm_resource) == 4

    def is_powered_off(self, vm_resource=None):
        """Checks if a vm is powered off or not.

        :param lxml.objectify.ObjectifiedElement vm_resource: object
            containing EntityType.VM XML data representing the vm whose
            power state we want to check.

        :return: True if the vm is powered off else False.

        :rtype: bool
        """
        return self.get_power_state(vm_resource) == 8

    def is_suspended(self, vm_resource=None):
        """Checks if a vm is suspended or not.

        :param lxml.objectify.ObjectifiedElement vm_resource: object
            containing EntityType.VM XML data representing the vm whose
            power state we want to check.

        :return: True if the vm is suspended else False.

        :rtype: bool
        """
        return self.get_power_state(vm_resource) == 3

    def is_deployed(self, vm_resource=None):
        """Checks if a vm is deployed or not.

        :param lxml.objectify.ObjectifiedElement vm_resource: object
            containing EntityType.VM XML data representing the vm whose
            power state we want to check.

        :return: True if the vm is deployed else False.

        :rtype: bool
        """
        return self.get_power_state(vm_resource) == 2

    def _perform_power_operation(self,
                                 rel,
                                 operation_name,
                                 media_type=None,
                                 contents=None):
        """Perform a power operation on the vm.

        Perform one of the following power operations on the vm.
        Power on, Power off, Deploy, Undeploy, Shutdown, Reboot, Power reset.

        :param pyvcloud.vcd.client.RelationType rel: relation of the link in
            the vm resource that will be triggered for the power operation.
        :param str operation_name: name of the power operation to perform. This
            value will be used while logging error messages (if any).
        :param str media_type: media type of the link in
            the vm resource that will be triggered for the power operation.
        :param lxml.objectify.ObjectifiedElement contents: payload for the
            linked operation.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is tracking the power operation on the
            vm.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises OperationNotSupportedException: if the power operation can't be
            performed on the vm.
        """
        vm_resource = self.get_resource()
        try:
            return self.client.post_linked_resource(vm_resource, rel,
                                                    media_type, contents)
        except OperationNotSupportedException:
            power_state = self.get_power_state(vm_resource)
            raise OperationNotSupportedException(
                'Can\'t {0} vm. Current state of vm: {1}.'.format(
                    operation_name, VCLOUD_STATUS_MAP[power_state]))

    def shutdown(self):
        """Shutdown the vm.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task shutting down the vm.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        return self._perform_power_operation(
            rel=RelationType.POWER_SHUTDOWN, operation_name='shutdown')

    def reboot(self):
        """Reboots the vm.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task rebooting the vm.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        return self._perform_power_operation(
            rel=RelationType.POWER_REBOOT, operation_name='reboot')

    def power_on(self):
        """Powers on the vm.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is powering on the vm.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        return self._perform_power_operation(
            rel=RelationType.POWER_ON, operation_name='power on')

    def power_off(self):
        """Powers off the vm.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is powering off the vm.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        return self._perform_power_operation(
            rel=RelationType.POWER_OFF, operation_name='power off')

    def power_reset(self):
        """Powers reset the vm.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is power resetting the vm.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        return self._perform_power_operation(
            rel=RelationType.POWER_RESET, operation_name='power reset')

    def deploy(self, power_on=True, force_customization=False):
        """Deploys the vm.

        Deploying the vm will allocate all resources assigned to the vm. If an
        attempt is made to deploy an already deployed vm, an exception will be
        raised.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is deploying the vm.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        deploy_vm_params = E.DeployVAppParams()
        deploy_vm_params.set('powerOn', str(power_on).lower())
        deploy_vm_params.set('forceCustomization',
                             str(force_customization).lower())
        return self._perform_power_operation(
            rel=RelationType.DEPLOY,
            operation_name='deploy',
            media_type=EntityType.DEPLOY.value,
            contents=deploy_vm_params)

    def undeploy(self, action='default'):
        """Undeploy the vm.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is undeploying the vm.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        params = E.UndeployVAppParams(E.UndeployPowerAction(action))
        return self._perform_power_operation(
            rel=RelationType.UNDEPLOY,
            operation_name='undeploy',
            media_type=EntityType.UNDEPLOY.value,
            contents=params)

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
        self.get_resource()
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
        self.get_resource()
        return self.client.post_linked_resource(
            self.resource, RelationType.SNAPSHOT_REVERT_TO_CURRENT, None, None)

    def snapshot_remove_all(self):
        """Removes all user created snapshots of a virtual machine.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task removing the snapshots.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        self.get_resource()
        return self.client.post_linked_resource(
            self.resource, RelationType.SNAPSHOT_REMOVE_ALL, None, None)

    def add_nic(self, adapter_type, is_primary, is_connected, network_name,
                ip_address_mode, ip_address):
        """Adds a nic to the VM.

        :param str adapter_type: nic adapter type.
            One of NetworkAdapterType values.
        :param bool is_primary: True, if its a primary nic of the VM.
        :param bool is_connected: True, if the nic has to be connected.
        :param str network_name: name of the network to be connected to.
        :param str ip_address_mode: One of DHCP|POOL|MANUAL|NONE.
        :param str ip_address: to be set an ip in case of MANUAL mode.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task adding  a nic.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        # get network connection section.
        net_conn_section = self.get_resource().NetworkConnectionSection
        nic_index = 0
        insert_index = net_conn_section.index(
            net_conn_section['{' + NSMAP['ovf'] + '}Info']) + 1
        # check if any nics exists
        if hasattr(net_conn_section, 'PrimaryNetworkConnectionIndex'):
            # calculate nic index and create the networkconnection object.
            indices = [None] * 10
            insert_index = net_conn_section.index(
                net_conn_section.PrimaryNetworkConnectionIndex) + 1
            for nc in net_conn_section.NetworkConnection:
                indices[int(nc.NetworkConnectionIndex.
                            text)] = nc.NetworkConnectionIndex.text
            nic_index = indices.index(None)
            if is_primary:
                net_conn_section.PrimaryNetworkConnectionIndex = \
                    E.PrimaryNetworkConnectionIndex(nic_index)

        net_conn = E.NetworkConnection(network=network_name)
        net_conn.append(E.NetworkConnectionIndex(nic_index))
        net_conn.append(E.IsConnected(is_connected))
        net_conn.append(E.IpAddressAllocationMode(ip_address_mode))
        net_conn.append(E.NetworkAdapterType(adapter_type))
        if ip_address_mode == IpAddressMode.MANUAL:
            net_conn.append(E.IpAddress(ip_address))

        net_conn_section.insert(insert_index, net_conn)
        return self.client.put_linked_resource(
            net_conn_section, RelationType.EDIT,
            EntityType.NETWORK_CONNECTION_SECTION.value, net_conn_section)

    def list_nics(self):
        """Lists all the nics of the VM.

        :return: list of nics with the following properties as a dictionary.
            nic index, is primary, is connected, connected network,
            ip address allocation mode, ip address, network adapter type

        :rtype: list
        """
        nics = []
        self.get_resource()
        if hasattr(self.resource.NetworkConnectionSection,
                   'PrimaryNetworkConnectionIndex'):
            primary_index = self.resource.NetworkConnectionSection.\
                PrimaryNetworkConnectionIndex.text

        for nc in self.resource.NetworkConnectionSection.NetworkConnection:
            nic = {}
            nic[VmNicProperties.INDEX.value] = nc.NetworkConnectionIndex.text
            nic[VmNicProperties.CONNECTED.value] = nc.IsConnected.text
            nic[VmNicProperties.PRIMARY.value] = (
                primary_index == nc.NetworkConnectionIndex.text)
            nic[VmNicProperties.ADAPTER_TYPE.
                value] = nc.NetworkAdapterType.text
            nic[VmNicProperties.NETWORK.value] = nc.get(
                VmNicProperties.NETWORK.value)
            nic[VmNicProperties.IP_ADDRESS_MODE.
                value] = nc.IpAddressAllocationMode.text
            if hasattr(nc, 'IpAddress'):
                nic[VmNicProperties.IP_ADDRESS.value] = nc.IpAddress.text
            nics.append(nic)
        return nics
