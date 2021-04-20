# VMware vCloud Director Python SDK
# Copyright (c) 2014-2018 VMware, Inc. All Rights Reserved.
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

from copy import deepcopy

from lxml import etree
from lxml import objectify

from pyvcloud.vcd.acl import Acl
from pyvcloud.vcd.client import E
from pyvcloud.vcd.client import E_OVF
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import FenceMode
from pyvcloud.vcd.client import find_link
from pyvcloud.vcd.client import get_logger
from pyvcloud.vcd.client import MetadataDomain
from pyvcloud.vcd.client import MetadataValueType
from pyvcloud.vcd.client import MetadataVisibility
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.client import VCLOUD_STATUS_MAP
from pyvcloud.vcd.exceptions import EntityNotFoundException
from pyvcloud.vcd.exceptions import InvalidParameterException
from pyvcloud.vcd.exceptions import InvalidStateException
from pyvcloud.vcd.exceptions import OperationNotSupportedException
from pyvcloud.vcd.metadata import Metadata
from pyvcloud.vcd.utils import cidr_to_netmask
from pyvcloud.vcd.utils import generate_compute_policy_tags
from pyvcloud.vcd.vdc import VDC
from pyvcloud.vcd.vm import VM

DEFAULT_CHUNK_SIZE = 10 * 1024 * 1024
LOGGER = get_logger()


class VApp(object):
    def __init__(self, client, name=None, href=None, resource=None):
        """Constructor for VApp objects.

        :param pyvcloud.vcd.client.Client client: the client that will be used
            to make REST calls to vCD.
        :param str name: name of the entity.
        :param str href: URI of the entity.
        :param lxml.objectify.ObjectifiedElement resource: object containing
            EntityType.VAPP XML data representing the vApp.
        """
        self.client = client
        self.name = name
        if href is None and resource is None:
            raise InvalidParameterException(
                "VApp initialization failed as arguments are either invalid "
                "or None")
        self.href = href
        self.resource = resource
        if resource is not None:
            self.name = resource.get('name')
            self.href = resource.get('href')

    def get_resource(self):
        """Fetches the XML representation of the vApp from vCD.

        Will serve cached response if possible.

        :return: object containing EntityType.VAPP XML data representing the
            vApp.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.reload()
        return self.resource

    def reload(self):
        """Reloads the resource representation of the vApp.

        This method should be called in between two method invocations on the
        VApp object, if the former call changes the representation of the
        vApp in vCD.
        """
        self.resource = self.client.get_resource(self.href)
        if self.resource is not None:
            self.name = self.resource.get('name')
            self.href = self.resource.get('href')

    def get_primary_ip(self, vm_name):
        """Fetch the primary ip of a vm (in the vApp) identified by its name.

        :param str vm_name: name of the vm whose primary ip we want to
            retrieve.

        :return: ip address of the named vm.

        :rtype: str

        :raises: Exception: if the named vm or its NIC information can't be
            found.
        """
        self.get_resource()
        if hasattr(self.resource, 'Children') and \
           hasattr(self.resource.Children, 'Vm'):
            for vm in self.resource.Children.Vm:
                if vm_name == vm.get('name'):
                    items = vm.xpath(
                        'ovf:VirtualHardwareSection/ovf:Item',
                        namespaces=NSMAP)
                    for item in items:
                        connection = item.find('rasd:Connection', NSMAP)
                        if connection is not None:
                            return connection.get('{' + NSMAP['vcloud'] +
                                                  '}ipAddress')
        raise Exception('can\'t find ip address')

    def get_admin_password(self, vm_name):
        """Fetch the admin password of a named vm in the vApp.

        :param str vm_name: name of the vm whose admin password we want to
            retrieve.

        :return: admin password of the named vm.

        :rtype: str

        :raises: EntityNotFoundException: if the named vm can't be found.
        """
        self.get_resource()
        if hasattr(self.resource, 'Children') and \
           hasattr(self.resource.Children, 'Vm'):
            for vm in self.resource.Children.Vm:
                if vm_name == vm.get('name'):
                    if hasattr(vm, 'GuestCustomizationSection') and \
                       hasattr(vm.GuestCustomizationSection, 'AdminPassword'):
                        return vm.GuestCustomizationSection.AdminPassword.text
        raise EntityNotFoundException('Can\'t find admin password')

    def get_metadata(self):
        """Fetch metadata of the vApp.

        :return: an object containing EntityType.METADATA XML data which
            represents the metadata associated with the vApp.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        self.get_resource()
        return self.client.get_linked_resource(
            self.resource, RelationType.DOWN, EntityType.METADATA.value)

    def set_metadata(self,
                     domain,
                     visibility,
                     key,
                     value,
                     metadata_type=MetadataValueType.STRING.value):
        """Add a new metadata entry to the vApp.

        If an entry with the same key exists, it will be updated with the new
        value.

        :param str domain: a value of SYSTEM places this MetadataEntry in the
            SYSTEM domain. Omit or leave empty to place this MetadataEntry in
            the GENERAL domain.
        :param str visibility: must be one of the values specified in
            MetadataVisibility enum.
        :param str key: an arbitrary key name. Length cannot exceed 256 UTF-8
            characters.
        :param str value: value of the metadata entry.
        :param str metadata_type: one of the types specified in
            client.MetadataValueType enum.

        :return: an object of type EntityType.TASK XML which represents
             the asynchronous task that is updating the metadata on the vApp.
        """
        metadata = Metadata(client=self.client, resource=self.get_metadata())
        return metadata.set_metadata(
            key=key,
            value=value,
            domain=MetadataDomain(domain),
            visibility=MetadataVisibility(visibility),
            metadata_value_type=MetadataValueType(metadata_type),
            use_admin_endpoint=False)

    def set_multiple_metadata(self,
                              key_value_dict,
                              domain=MetadataDomain.GENERAL,
                              visibility=MetadataVisibility.READ_WRITE,
                              metadata_value_type=MetadataValueType.STRING):
        """Add multiple new metadata entries to the vApp.

        If an entry with the same key exists, it will be updated with the new
        value. All entries must have the same value type and will be written to
        the same domain with identical visibility.

        :param dict key_value_dict: a dict containing key-value pairs to be
            added/updated.
        :param client.MetadataDomain domain: domain where the new entries would
            be put.
        :param client.MetadataVisibility visibility: visibility of the metadata
            entries.
        :param client.MetadataValueType metadata_value_type:

        :return: an object of type EntityType.TASK XML which represents
             the asynchronous task that is updating the metadata on the vApp.
        """
        metadata = Metadata(client=self.client, resource=self.get_metadata())
        return metadata.set_multiple_metadata(
            key_value_dict=key_value_dict,
            domain=MetadataDomain(domain),
            visibility=MetadataVisibility(visibility),
            metadata_value_type=MetadataValueType(metadata_value_type),
            use_admin_endpoint=False)

    def remove_metadata(self, key, domain=MetadataDomain.GENERAL):
        """Remove a metadata entry from the vApp.

        :param str key: key of the metadata to be removed.
        :param client.MetadataDomain domain: domain of the entry to be removed.

        :return: an object of type EntityType.TASK XML which represents
            the asynchronous task that is deleting the metadata on the vApp.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: AccessForbiddenException: If there is no metadata entry
            corresponding to the key provided.
        """
        metadata = Metadata(client=self.client, resource=self.get_metadata())
        return metadata.remove_metadata(
            key=key, domain=domain, use_admin_endpoint=False)

    def get_vm_moid(self, vm_name):
        """Fetch the moref of a named vm in the vApp.

        :param str vm_name: name of the vm whose moref  we want to retrieve.

        :return: moref of the named vm.

        :rtype: str

        :raises: EntityNotFoundException: if the named vm can't be found.
        """
        vapp = self.get_resource()
        if hasattr(vapp, 'Children') and hasattr(vapp.Children, 'Vm'):
            for vm in vapp.Children.Vm:
                if vm.get('name') == vm_name:
                    env = vm.xpath('ovfenv:Environment', namespaces=NSMAP)
                    if len(env) > 0:
                        return env[0].get('{' + NSMAP['ve'] + '}vCenterId')
        return None

    def set_lease(self, deployment_lease=0, storage_lease=0):
        """Update lease settings of the vApp.

        :param int deployment_lease: length of deployment lease in seconds.
        :param int storage_lease: length of storage lease in seconds.

        :return: an object containing EntityType.LEASE_SETTINGS XML data which
            represents the updated lease settings of the vApp.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        self.get_resource()
        new_section = self.resource.LeaseSettingsSection

        new_section.DeploymentLeaseInSeconds = deployment_lease
        new_section.StorageLeaseInSeconds = storage_lease
        objectify.deannotate(new_section)
        etree.cleanup_namespaces(new_section)
        return self.client.put_resource(
            self.resource.get('href') + '/leaseSettingsSection/', new_section,
            EntityType.LEASE_SETTINGS.value)

    def get_lease(self):
        """Fetch lease settings data of the vApp.

        :return: an dictionary containing LEASE_SETTINGS Data of the vApp.

        :rtype: dict
        """
        self.get_resource()
        lease_setting = self.resource.LeaseSettingsSection
        result = {}
        if hasattr(lease_setting, 'DeploymentLeaseInSeconds'):
            result['DeploymentLeaseInSeconds'] = \
                lease_setting.DeploymentLeaseInSeconds
        if hasattr(lease_setting, 'StorageLeaseInSeconds'):
            result['StorageLeaseInSeconds'] = \
                lease_setting.StorageLeaseInSeconds
        if hasattr(lease_setting, 'StorageLeaseExpiration'):
            result['StorageLeaseExpiration'] = \
                lease_setting.StorageLeaseExpiration
        return result

    def change_owner(self, href):
        """Change the ownership of vApp to a given user.

        :param str href: href of the new owner.
        """
        self.get_resource()
        new_owner = self.resource.Owner
        new_owner.User.set('href', href)
        objectify.deannotate(new_owner)
        etree.cleanup_namespaces(new_owner)
        return self.client.put_resource(
            self.resource.get('href') + '/owner/', new_owner,
            EntityType.OWNER.value)

    def get_power_state(self, vapp_resource=None):
        """Returns the status of the vApp.

        :param lxml.objectify.ObjectifiedElement vapp_resource: object
            containing EntityType.VAPP XML data representing the vApp whose
            power state we want to retrieve.

        :return: The status of the vApp, the semantics of the value returned is
            captured in pyvcloud.vcd.client.VCLOUD_STATUS_MAP

        :rtype: int
        """
        if vapp_resource is None:
            vapp_resource = self.get_resource()
        return int(vapp_resource.get('status'))

    def is_powered_on(self, vapp_resource=None):
        """Checks if a vApp is powered on or not.

        :param lxml.objectify.ObjectifiedElement vapp_resource: object
            containing EntityType.VAPP XML data representing the vApp whose
            power state we want to check.

        :return: True if the vApp is powered on else False.

        :rtype: bool
        """
        return self.get_power_state(vapp_resource) == 4

    def is_powered_off(self, vapp_resource=None):
        """Checks if a vApp is powered off or not.

        :param lxml.objectify.ObjectifiedElement vapp_resource: object
            containing EntityType.VAPP XML data representing the vApp whose
            power state we want to check.

        :return: True if the vApp is powered off else False.

        :rtype: bool
        """
        return self.get_power_state(vapp_resource) == 8

    def is_suspended(self, vapp_resource=None):
        """Checks if a vApp is suspended or not.

        :param lxml.objectify.ObjectifiedElement vapp_resource: object
            containing EntityType.VAPP XML data representing the vApp whose
            power state we want to check.

        :return: True if the vApp is suspended else False.

        :rtype: bool
        """
        return self.get_power_state(vapp_resource) == 3

    def is_deployed(self, vapp_resource=None):
        """Checks if a vApp is deployed or not.

        :param lxml.objectify.ObjectifiedElement vapp_resource: object
            containing EntityType.VAPP XML data representing the vApp whose
            power state we want to check.

        :return: True if the vApp is deployed else False.

        :rtype: bool
        """
        return self.get_power_state(vapp_resource) == 2

    def _perform_power_operation(self,
                                 rel,
                                 operation_name,
                                 media_type=None,
                                 contents=None):
        """Perform a power operation on the vApp.

        Perform one of the following power operations on the vApp.
        Power on, Power off, Deploy, Undeploy, Shutdown, Reboot, Power reset.

        :param pyvcloud.vcd.client.RelationType rel: relation of the link in
            the vApp resource that will be triggered for the power operation.
        :param str operation_name: name of the power operation to perform. This
            value will be used while logging error messages (if any).
        :param str media_type: media type of the link in
            the vApp resource that will be triggered for the power operation.
        :param lxml.objectify.ObjectifiedElement contents: payload for the
            linked operation.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is tracking the power operation on the
            vApp.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises OperationNotSupportedException: if the power operation can't be
            performed on the vApp.
        """
        vapp_resource = self.get_resource()
        try:
            return self.client.post_linked_resource(vapp_resource, rel,
                                                    media_type, contents)
        except OperationNotSupportedException:
            power_state = self.get_power_state(vapp_resource)
            raise OperationNotSupportedException(
                'Can\'t {0} vApp. Current state of vApp: {1}.'.format(
                    operation_name, VCLOUD_STATUS_MAP[power_state]))

    def deploy(self, power_on=None, force_customization=None):
        """Deploys the vApp.

        Deploying the vApp will allocate all resources assigned to the vApp.
        TODO: Add lease_deployment_seconds param after PR 2036925 is fixed.
        https://jira.eng.vmware.com/browse/VCDA-465

        :param bool power_on: specifies whether to power on/off vApp/vm
            on deployment. True by default, unless otherwise specified.
        :param str lease_deployment_seconds: deployment lease in seconds.
        :param bool force_customization: True, instructs vCD to force
            customization on deployment. False, no action is performed.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is deploying the vApp.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises OperationNotSupportedException: if the vApp can't be deployed.
        """
        deploy_vapp_params = E.DeployVAppParams()
        if power_on is not None:
            deploy_vapp_params.set('powerOn', str(power_on).lower())
        if force_customization is not None:
            deploy_vapp_params.set('forceCustomization',
                                   str(force_customization).lower())

        return self._perform_power_operation(
            rel=RelationType.DEPLOY,
            operation_name='deploy',
            media_type=EntityType.DEPLOY.value,
            contents=deploy_vapp_params)

    def undeploy(self, action='default'):
        """Undeploys the vApp.

        :param str action: specifies the action to be applied to all vms in the
            vApp. Accepted values are

                - powerOff: power off the virtual machines.
                - suspend: suspend the virtual machines.
                - shutdown: shut down the virtual machines.
                - force: attempt to power off the virtual machines. Failures in
                    undeploying the virtual machine or associated networks are
                    ignored. All references to the vApp and its vms are removed
                    from the database.
                - default: use the actions, order, and delay specified in the
                    StartupSection.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is undeploying the vApp.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises OperationNotSupportedException: if the vApp can't be
            undeployed.
        """
        params = E.UndeployVAppParams(E.UndeployPowerAction(action))

        return self._perform_power_operation(
            rel=RelationType.UNDEPLOY,
            operation_name='undeploy',
            media_type=EntityType.UNDEPLOY.value,
            contents=params)

    def power_off(self):
        """Power off the vms in the vApp.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is powering off the vApp.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises OperationNotSupportedException: if the vApp can't be powered
            off.
        """
        return self._perform_power_operation(
            rel=RelationType.POWER_OFF, operation_name='power off')

    def power_on(self):
        """Power on the vms in the vApp.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is powering on the vApp.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises OperationNotSupportedException: if the vApp can't be powered
            on.
        """
        return self._perform_power_operation(
            rel=RelationType.POWER_ON, operation_name='power on')

    def shutdown(self):
        """Shutdown the vApp.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task shutting down the vApp.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises OperationNotSupportedException: if the vApp can't be shutdown.
        """
        return self._perform_power_operation(
            rel=RelationType.POWER_SHUTDOWN, operation_name='shutdown')

    def power_reset(self):
        """Power resets the vms in the vApp.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task resetting the vApp.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises OperationNotSupportedException: if the vApp can't be power
            reset.
        """
        return self._perform_power_operation(
            rel=RelationType.POWER_RESET, operation_name='power reset')

    def reboot(self):
        """Reboots the vms in the vApp.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task rebooting the vApp.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises OperationNotSupportedException: if the vApp can't be rebooted.
        """
        return self._perform_power_operation(
            rel=RelationType.POWER_REBOOT, operation_name='reboot')

    def connect_vm(self, mode='DHCP', reset_mac_address=False):
        self.get_resource()
        if hasattr(self.resource, 'Children') and \
           hasattr(self.resource.Children, 'Vm') and \
           len(self.resource.Children.Vm) > 0:
            network_name = 'none'
            for nc in self.resource.NetworkConfigSection.NetworkConfig:
                if nc.get('networkName') != 'none':
                    network_name = nc.get('networkName')
                    break
            self.resource.Children.Vm[
                0].NetworkConnectionSection.NetworkConnection.set(
                    'network', network_name)
            self.resource.Children.Vm[
                0].NetworkConnectionSection.NetworkConnection.IsConnected = \
                E.IsConnected('true')
            if reset_mac_address:
                self.resource.Children.Vm[0].NetworkConnectionSection.\
                    NetworkConnection.MACAddress = E.MACAddress('')
            self.resource.Children.Vm[0].NetworkConnectionSection.\
                NetworkConnection.IpAddressAllocationMode = \
                E.IpAddressAllocationMode(mode.upper())
            return self.client.put_linked_resource(
                self.resource.Children.Vm[0].NetworkConnectionSection,
                RelationType.EDIT, EntityType.NETWORK_CONNECTION_SECTION.value,
                self.resource.Children.Vm[0].NetworkConnectionSection)

    def attach_disk_to_vm(self, disk_href, vm_name):
        """Attach an independent disk to the vm with the given name.

        :param str disk_href: href of the disk to be attached.
        :param str vm_name: name of the vm to which the disk will be attached.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task of attaching the disk.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: EntityNotFoundException: if the named vm or disk cannot be
            located.
        """
        disk_attach_or_detach_params = E.DiskAttachOrDetachParams(
            E.Disk(type=EntityType.DISK.value, href=disk_href))
        vm = self.get_vm(vm_name)

        return self.client.post_linked_resource(
            vm, RelationType.DISK_ATTACH,
            EntityType.DISK_ATTACH_DETACH_PARAMS.value,
            disk_attach_or_detach_params)

    def detach_disk_from_vm(self, disk_href, vm_name):
        """Detach the independent disk from the vm with the given name.

        :param str disk_href: href of the disk to be detached.
        :param str vm_name: name of the vm to which the disk will be detached.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task of dettaching the disk.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: EntityNotFoundException: if the named vm or disk cannot be
            located.
        """
        disk_attach_or_detach_params = E.DiskAttachOrDetachParams(
            E.Disk(type=EntityType.DISK.value, href=disk_href))
        vm = self.get_vm(vm_name)
        return self.client.post_linked_resource(
            vm, RelationType.DISK_DETACH,
            EntityType.DISK_ATTACH_DETACH_PARAMS.value,
            disk_attach_or_detach_params)

    def get_all_vms(self):
        """Retrieve all the vms in the vApp.

        :return: a list of lxml.objectify.ObjectifiedElement objects, where
            each object contains EntityType.VM XML data and represents one vm.

        :rtype: empty list or generator object
        """
        self.get_resource()
        if hasattr(self.resource, 'Children') and \
                hasattr(self.resource.Children, 'Vm') and \
                len(self.resource.Children.Vm) > 0:
            return self.resource.Children.Vm
        else:
            return []

    def get_vm(self, vm_name):
        """Retrieve the vm with the given name in this vApp.

        :param str vm_name: name of the vm to be retrieved.

        :return: an object contains EntityType.VM XML data that represents the
            vm.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: EntityNotFoundException: if the named vm could not be found.
        """
        for vm in self.get_all_vms():
            if vm.get('name') == vm_name:
                return vm
        raise EntityNotFoundException('Can\'t find VM \'%s\'' % vm_name)

    def add_disk_to_vm(self, vm_name, disk_size, disk_controller="lsilogic"):
        """Add a virtual disk to a virtual machine in the vApp.

        It assumes that the vm has already at least one virtual hard disk
        and will attempt to create another one with similar characteristics.

        :param str vm_name: name of the vm to be customized.
        :param int disk_size: size of the disk to be added, in MBs.
        :param str disk_controller: name of the disk controller.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is creating the disk.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: EntityNotFoundException: if the named vm cannot be located.
            occurred.
        """
        disk_index = 0
        last_disk = None
        vm = self.get_vm(vm_name)
        scsi_controller_bus_type = 6
        # supported disk controllers to add
        # default disk controller and addresses are,
        # VirtualSCSI  address 0
        # lsilogicsas  address 1
        # lsilogic     address 2
        # buslogic     address 3
        scsi_disk_controllers = [
            "VirtualSCSI", "lsilogic", "lsilogicsas", "buslogic"]
        is_disk_controller_present = False
        disks = self.client.get_resource(
            vm.get('href') + '/virtualHardwareSection/disks')

        for disk in disks.Item:
            element_name = str(disk['{' + NSMAP['rasd'] + '}ElementName'])
            # recording last disk to update as a new disk
            if disk['{' + NSMAP['rasd'] + '}Description'] == 'Hard disk':
                last_disk = disk
                disk_index += 1

            # updating default disk controller's address with existing
            # disk controller's address if any
            if "SCSI Controller" in str(element_name):
                addr = int(disk['{' + NSMAP['rasd'] + '}Address'])
                bus_type = disk['{' + NSMAP['rasd'] + '}ResourceSubType']
                expected_addr = scsi_disk_controllers.index(bus_type)
                scsi_disk_controllers[addr], scsi_disk_controllers[
                    expected_addr] = scsi_disk_controllers[expected_addr],\
                    scsi_disk_controllers[addr]

            # look for SCSI disk controller if present
            resource_type = int(disk['{' + NSMAP['rasd'] + '}ResourceType'])
            if resource_type == scsi_controller_bus_type:
                if disk_controller == str(disk[
                        '{' + NSMAP['rasd'] + '}ResourceSubType']):
                    is_disk_controller_present = True

        new_disk = deepcopy(last_disk)
        instance_id = int(str(last_disk[
            '{' + NSMAP['rasd'] + '}InstanceID'])) + 1
        address = int(str(last_disk[
            '{' + NSMAP['rasd'] + '}AddressOnParent'])) + 1

        if not is_disk_controller_present:
            # create a new SCSI controller
            address = scsi_disk_controllers.index(disk_controller)
            new_disk_controller = self._create_scsi_disk_controller(
                last_disk, disk_controller)
            new_disk_controller['{' + NSMAP['rasd'] + '}Address'] = address
            new_disk['{' + NSMAP['rasd'] + '}Parent'] = new_disk_controller[
                '{' + NSMAP['rasd'] + '}InstanceID']
            disks.append(new_disk_controller)

        # create a new disk
        new_disk['{' + NSMAP['rasd'] + '}AddressOnParent'] = address
        new_disk[
            '{' + NSMAP['rasd'] + '}ElementName'] = 'Hard disk %s' % disk_index
        new_disk[
            '{' + NSMAP['rasd'] + '}InstanceID'] = instance_id
        new_disk[
            '{' + NSMAP['rasd'] + '}VirtualQuantity'] = disk_size * 1024 * 1024
        new_disk['{' + NSMAP['rasd'] + '}HostResource'].set(
            '{' + NSMAP['vcloud'] + '}capacity', str(disk_size))
        new_disk['{' + NSMAP['rasd'] + '}HostResource'].set(
            '{' + NSMAP['vcloud'] + '}busSubType', disk_controller)
        new_disk['{' + NSMAP['rasd'] + '}HostResource'].set(
            '{' + NSMAP['vcloud'] + '}busType', str(scsi_controller_bus_type))
        disks.append(new_disk)

        return self.client.put_resource(
            vm.get('href') + '/virtualHardwareSection/disks',
            disks, EntityType.RASD_ITEMS_LIST.value)

    def _create_scsi_disk_controller(self, last_disk, disk_controller):
        """Create a new SCSI disk controller to a virtual machine in the vApp.

        :param lxml.objectify.ObjectifiedElement last_disk: A disk object
        already attached to a VM.
        :param str disk_controller: name of the disk controller.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        new_disk_controller = deepcopy(last_disk)
        new_disk_controller['{' + NSMAP['rasd'] + '}ResourceType'] = 6
        new_disk_controller[
            '{' + NSMAP['rasd'] + '}ResourceSubType'] = disk_controller

        return new_disk_controller

    def get_access_settings(self):
        """Get the access settings of the vApp.

        :return: an object containing EntityType.CONTROL_ACCESS_PARAMS which
            represents the access control list of the vApp.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        acl = Acl(self.client, self.get_resource())
        return acl.get_access_settings()

    def add_access_settings(self, access_settings_list=None):
        """Add access settings to the vApp.

        :param list access_settings_list: list of dictionaries, where each
            dictionary represents a single access setting. The dictionary
            structure is as follows,

            - type: (str): type of the subject. One of 'org' or 'user'.
            - name: (str): name of the user or org.
            - access_level: (str): access_level of the particular subject.
                Allowed values are 'ReadOnly', 'Change' or 'FullControl'.

        :return: an object containing EntityType.CONTROL_ACCESS_PARAMS XML
            data representing the updated Access Control List of the vApp.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        acl = Acl(self.client, self.get_resource())
        return acl.add_access_settings(access_settings_list)

    def remove_access_settings(self,
                               access_settings_list=None,
                               remove_all=False):
        """Remove access settings from the vApp.

        :param list access_settings_list: list of dictionaries, where each
            dictionary represents a single access setting. The dictionary
            structure is as follows,

            - type: (str): type of the subject. One of 'org' or 'user'.
            - name: (str): name of the user or org.
        :param bool remove_all: True, if the entire Access Control List of the
            vApp should be removed, else False.

        :return: an object containing EntityType.CONTROL_ACCESS_PARAMS XML
            data representing the updated access control setting of the vdc.

        :rtype: lxml.objectify.ObjectifiedElement`
        """
        acl = Acl(self.client, self.get_resource())
        return acl.remove_access_settings(access_settings_list, remove_all)

    def share_with_org_members(self, everyone_access_level='ReadOnly'):
        """Share the vApp to all members of the organization.

        :param everyone_access_level: (str) : access level when sharing the
            vApp with everyone. Allowed values are 'ReadOnly', 'Change', or
            'FullControl'. Default value is 'ReadOnly'.

        :return: an object containing EntityType.CONTROL_ACCESS_PARAMS XML
            data representing the updated access control setting of the vdc.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        acl = Acl(self.client, self.get_resource())
        return acl.share_with_org_members(everyone_access_level)

    def unshare_from_org_members(self):
        """Unshare the vApp from all members of current organization.

        :return: an object containing EntityType.CONTROL_ACCESS_PARAMS XML
            data representing the updated access control setting of the vdc.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        acl = Acl(self.client, self.get_resource())
        return acl.unshare_from_org_members()

    def get_all_networks(self):
        """Helper method that returns the list of networks defined in the vApp.

        :return: a smart xpath string that represents the list of vApp
            networks.

        :rtype: xpath string
        """
        self.get_resource()
        return self.resource.xpath(
            '//ovf:NetworkSection/ovf:Network',
            namespaces={'ovf': NSMAP['ovf']})

    def get_vapp_network_name(self, index=0):
        """Returns the name of the network defined in the vApp by index.

        :param int index: index of the vApp network to retrieve. 0 if omitted.

        :return: name of the requested network.

        :rtype: str

        :raises: EntityNotFoundException: if the named network could not be
            found.
        """
        networks = self.get_all_networks()
        if networks is None or len(networks) < index + 1:
            raise EntityNotFoundException(
                'Can\'t find the specified vApp network')
        return networks[index].get('{' + NSMAP['ovf'] + '}name')

    def to_sourced_item(self, spec):
        """Creates a vm SourcedItem from a vm specification.

        :param dict spec: a dictionary containing

            - vapp: (resource): (required) source vApp or vAppTemplate
                resource.
            - source_vm_name: (str): (required) source vm name.
            - target_vm_name: (str): (optional) target vm name.
            - hostname: (str): (optional) target guest hostname.
            - password: (str): (optional) the administrator password of the vm.
            - password_auto: (bool): (optional) auto generate administrator
                password.
            - password_reset: (bool): (optional) True, if the administrator
                password for this vm must be reset after first use.
            - cust_script: (str): (optional) script to run on guest
                customization.
            - network: (str): (optional) name of the vApp network to connect.
                If omitted, the vm won't be connected to any network.
            - storage_profile: (str): (optional) the name of the storage
                profile to be used for this vm.
            - sizing_policy_href: (str): (optional) sizing policy used for
                creating the VM
            - placement_policy_href: (str): (optional) placement policy used
                for creating the VM

        :return: an object containing SourcedItem XML element.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        source_vapp = VApp(self.client, resource=spec['vapp'])
        source_vm_resource = source_vapp.get_vm(spec['source_vm_name'])

        sourced_item = E.SourcedItem(
            E.Source(
                href=source_vm_resource.get('href'),
                id=source_vm_resource.get('id'),
                name=source_vm_resource.get('name'),
                type=source_vm_resource.get('type')))

        vm_general_params = E.VmGeneralParams()
        if 'target_vm_name' in spec:
            vm_general_params.append(E.Name(spec['target_vm_name']))

        vm_instantiation_param = E.InstantiationParams()
        if 'network' in spec:
            primary_index = int(source_vm_resource.NetworkConnectionSection.
                                PrimaryNetworkConnectionIndex.text)
            if 'ip_allocation_mode' in spec:
                ip_allocation_mode = spec['ip_allocation_mode']
            else:
                ip_allocation_mode = 'DHCP'
            vm_instantiation_param.append(
                E.NetworkConnectionSection(
                    E_OVF.Info(),
                    E.NetworkConnection(
                        E.NetworkConnectionIndex(primary_index),
                        E.IsConnected(True),
                        E.IpAddressAllocationMode(ip_allocation_mode.upper()),
                        network=spec['network'])))

        needs_customization = 'disk_size' in spec or 'password' in spec or \
            'cust_script' in spec or 'hostname' in spec
        if needs_customization:
            guest_customization_param = E.GuestCustomizationSection(
                E_OVF.Info(),
                E.Enabled(True),
            )
            if 'password' in spec:
                guest_customization_param.append(E.AdminPasswordEnabled(True))
                guest_customization_param.append(E.AdminPasswordAuto(False))
                guest_customization_param.append(
                    E.AdminPassword(spec['password']))
            else:
                if 'password_auto' in spec:
                    guest_customization_param.append(
                        E.AdminPasswordEnabled(True))
                    guest_customization_param.append(E.AdminPasswordAuto(True))
                else:
                    guest_customization_param.append(
                        E.AdminPasswordEnabled(False))
            if 'password_reset' in spec:
                guest_customization_param.append(
                    E.ResetPasswordRequired(spec['password_reset']))
            if 'cust_script' in spec:
                guest_customization_param.append(
                    E.CustomizationScript(spec['cust_script']))
            if 'hostname' in spec:
                guest_customization_param.append(
                    E.ComputerName(spec['hostname']))
            vm_instantiation_param.append(guest_customization_param)

        vm_general_params.append(E.NeedsCustomization(needs_customization))
        sourced_item.append(vm_general_params)
        sourced_item.append(vm_instantiation_param)

        if 'storage_profile' in spec:
            sp = spec['storage_profile']
            storage_profile = E.StorageProfile(
                href=sp.get('href'),
                id=sp.get('href').split('/')[-1],
                type=sp.get('type'),
                name=sp.get('name'))
            sourced_item.append(storage_profile)

        vdc_compute_policy_element, compute_policy_element = \
            generate_compute_policy_tags(float(self.client.get_api_version()),
                                         sizing_policy_href=spec.get('sizing_policy_href'),  # noqa: E501
                                         placement_policy_href=spec.get('placement_policy_href'))  # noqa: E501
        if vdc_compute_policy_element is not None:
            sourced_item.append(vdc_compute_policy_element)
        if compute_policy_element is not None:
            sourced_item.append(compute_policy_element)

        return sourced_item

    def add_vms(self,
                specs,
                deploy=True,
                power_on=True,
                all_eulas_accepted=None,
                source_delete=False):
        """Recompose the vApp and add vms.

        :param dict specs: vm specifications, see `to_sourced_item()` method
            for specification details.
        :param bool deploy: True, if the vApp should be deployed at
            instantiation.
        :param power_on: (bool): True if the vApp should be powered-on at
            instantiation
        :param bool all_eulas_accepted: True confirms acceptance of all
            EULAs in the vApp.

        :return: an object containing EntityType.VAPP XML data representing the
            updated vApp.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        params = E.RecomposeVAppParams(
            deploy='true' if deploy else 'false',
            powerOn='true' if power_on else 'false')

        for spec in specs:
            params.append(self.to_sourced_item(spec))
        if source_delete:
            params.SourcedItem.set('sourceDelete', 'true')
        if all_eulas_accepted is not None:
            params.append(E.AllEULAsAccepted(all_eulas_accepted))
        return self.client.post_linked_resource(
            self.resource, RelationType.RECOMPOSE,
            EntityType.RECOMPOSE_VAPP_PARAMS.value, params)

    def delete_vms(self, names):
        """Recompose the vApp and delete vms.

        :param list names: names (str) of vms to delete from the vApp.

        :return: an object containing EntityType.VAPP XML data representing the
            updated vApp.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        params = E.RecomposeVAppParams()
        for name in names:
            vm = self.get_vm(name)
            params.append(E.DeleteItem(href=vm.get('href')))
        return self.client.post_linked_resource(
            self.resource, RelationType.RECOMPOSE,
            EntityType.RECOMPOSE_VAPP_PARAMS.value, params)

    def connect_org_vdc_network(self,
                                orgvdc_network_name,
                                retain_ip=None,
                                is_deployed=None,
                                fence_mode=FenceMode.BRIDGED.value):
        """Connect the vApp to an org vdc network.

        :param str orgvdc_network_name: name of the org vdc network to be
            connected to.
        :param bool retain_ip: True, if  the network resources such as IP/MAC
            of router will be retained across deployments.
        :param bool is_deployed: True, if this org vdc network has been
            deployed.
        :param str fence_mode: mode of connectivity to the parent network.
            Acceptable values are 'bridged', 'isolated' or 'natRouted'. Default
            value is 'bridged'.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task  that is connecting the vApp to the network.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: EntityNotFoundException: if named org vdc network does not
            exist.
        :raises: InvalidStateException: if the vApp is already connected to the
            org vdc network.
        """
        vdc = VDC(
            self.client,
            href=find_link(self.resource, RelationType.UP,
                           EntityType.VDC.value).href)
        orgvdc_network_href = vdc.get_orgvdc_network_admin_href_by_name(
            orgvdc_network_name)

        network_configuration_section = \
            deepcopy(self.resource.NetworkConfigSection)

        matched_orgvdc_network_config = \
            self._search_for_network_config_by_name(
                orgvdc_network_name, network_configuration_section)
        if matched_orgvdc_network_config is not None:
            raise InvalidStateException(
                "Org vdc network \'%s\' is already connected to "
                "vApp." % orgvdc_network_name)

        configuration = E.Configuration(
            E.ParentNetwork(href=orgvdc_network_href), E.FenceMode(fence_mode))
        if retain_ip is not None:
            configuration.append(E.RetainNetInfoAcrossDeployments(retain_ip))
        network_config = E.NetworkConfig(
            configuration, networkName=orgvdc_network_name)
        if is_deployed is not None:
            network_config.append(E.IsDeployed(is_deployed))
        network_configuration_section.append(network_config)

        return self.client.put_linked_resource(
            self.resource.NetworkConfigSection, RelationType.EDIT,
            EntityType.NETWORK_CONFIG_SECTION.value,
            network_configuration_section)

    def disconnect_org_vdc_network(self, orgvdc_network_name):
        """Disconnect the vApp from an org vdc network.

        :param str orgvdc_network_name: (str): name of the orgvdc network to be
            disconnected.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task  that is disconnecting the vApp from the
            network.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: InvalidStateException: if the named org vdc network is not
            connected to the vApp.
        """
        network_configuration_section = \
            deepcopy(self.resource.NetworkConfigSection)

        matched_orgvdc_network_config = \
            self._search_for_network_config_by_name(
                orgvdc_network_name, network_configuration_section)
        if matched_orgvdc_network_config is None:
            raise InvalidStateException(
                "Org vdc network \'%s\' is not attached to the vApp" %
                orgvdc_network_name)
        else:
            network_configuration_section.remove(matched_orgvdc_network_config)

        return self.client.put_linked_resource(
            self.resource.NetworkConfigSection, RelationType.EDIT,
            EntityType.NETWORK_CONFIG_SECTION.value,
            network_configuration_section)

    @staticmethod
    def _search_for_network_config_by_name(orgvdc_network_name,
                                           network_configuration_section):
        """Search for the NetworkConfig element by org vdc network name.

        :param str orgvdc_network_name: name of the org vdc network to be
            searched.
        :param lxml.objectify.ObjectifiedElement network_configuration_section:
            NetworkConfigSection of the vApp.

        :return: an object containing NetworkConfig XML element which
            represents the configuration of the named org vdc network.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if hasattr(network_configuration_section, 'NetworkConfig'):
            for network_config in network_configuration_section.NetworkConfig:
                if network_config.get('networkName') == orgvdc_network_name:
                    return network_config
        return None

    def create_vapp_network(self,
                            name,
                            network_cidr,
                            description=None,
                            primary_dns_ip=None,
                            secondary_dns_ip=None,
                            dns_suffix=None,
                            ip_ranges=None,
                            is_guest_vlan_allowed=False):
        """Create a vApp network.

        :param str network_name: name of vApp network to be created.
        :param str network_cidr: CIDR in the format of 192.168.1.1/24.
        :param str description: description of vApp network.
        :param str primary_dns_ip: IP address of primary DNS server.
        :param str secondary_dns_ip: IP address of secondary DNS Server.
        :param str dns_suffix: DNS suffix.
        :params list ip_ranges: list of IP ranges used for static pool
            allocation in the network. For example, [192.168.1.2-192.168.1.49,
            192.168.1.100-192.168.1.149].

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is creating the vApp network.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        self.get_resource()
        network_config_section = \
            deepcopy(self.resource.NetworkConfigSection)
        network_config = E.NetworkConfig(networkName=name)
        if description is not None:
            network_config.append(E.Description(description))

        config = E.Configuration()
        ip_scopes = E.IpScopes()
        ip_scope = E.IpScope()

        ip_scope.append(E.IsInherited(False))
        gateway_ip, netmask = cidr_to_netmask(network_cidr)
        ip_scope.append(E.Gateway(gateway_ip))
        ip_scope.append(E.Netmask(netmask))
        if primary_dns_ip is not None:
            ip_scope.append(E.Dns1(primary_dns_ip))
        if secondary_dns_ip is not None:
            ip_scope.append(E.Dns2(secondary_dns_ip))
        if dns_suffix is not None:
            ip_scope.append(E.DnsSuffix(dns_suffix))

        if ip_ranges is not None:
            e_ip_ranges = E.IpRanges()
            for ip_range in ip_ranges:
                e_ip_range = E.IpRange()
                ip_range_token = ip_range.split('-')
                e_ip_range.append(E.StartAddress(ip_range_token[0]))
                e_ip_range.append(E.EndAddress(ip_range_token[1]))
                e_ip_ranges.append(e_ip_range)

            ip_scope.append(e_ip_ranges)
        ip_scopes.append(ip_scope)
        config.append(ip_scopes)
        config.append(E.FenceMode(FenceMode.ISOLATED.value))
        config.append(E.GuestVlanAllowed(is_guest_vlan_allowed))
        network_config.append(config)

        network_config_section.append(network_config)
        return self.client.put_linked_resource(
            self.resource.NetworkConfigSection, RelationType.EDIT,
            EntityType.NETWORK_CONFIG_SECTION.value, network_config_section)

    def reset_vapp_network(self, network_name):
        """Resets a vApp network.

        :param str network_name: name of vApp network to be reset.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is resetting the vApp network.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        self.get_resource()
        # find the required network
        for nw in self.resource.NetworkConfigSection.NetworkConfig:
            if nw.get("networkName") == network_name:
                return self.client.post_linked_resource(
                    nw, RelationType.REPAIR, None, None)
        raise EntityNotFoundException(
            'Can\'t find network \'%s\'' % network_name)

    def delete_vapp_network(self, network_name):
        """Deletes a vApp network.

        :param str network_name: name of vApp network to be deleted.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is deleting the vApp network.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        self.get_resource()
        network_config_section = deepcopy(self.resource.NetworkConfigSection)
        # find the required network
        for nw in network_config_section.NetworkConfig:
            if nw.get("networkName") == network_name:
                network_config_section.remove(nw)
                return self.client.put_linked_resource(
                    self.resource.NetworkConfigSection, RelationType.EDIT,
                    EntityType.NETWORK_CONFIG_SECTION.value,
                    network_config_section)
        raise EntityNotFoundException(
            'Can\'t find network \'%s\'' % network_name)

    def update_vapp_network(self, network_name, new_net_name, new_net_desc):
        """Update a vApp network.

        :param str network_name: name of vApp network to be updated.
        :param str new_net_name: name of vApp network to be updated.
        :param str new_net_desc: description of vApp network to be updated.
        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is updating the vApp network.
        :rtype: lxml.objectify.ObjectifiedElement
        """
        # find the required network
        for network_config in self.resource.NetworkConfigSection.NetworkConfig:
            if network_config.get("networkName") == network_name:
                if new_net_name:
                    network_config.set('networkName', new_net_name)
                if new_net_desc:
                    if hasattr(network_config, 'Description'):
                        network_config.Description = E.Description(
                            new_net_desc)
                    else:
                        network_config.insert(0, E.Description(new_net_desc))
                return self.client.put_linked_resource(
                    self.resource.NetworkConfigSection, RelationType.EDIT,
                    EntityType.NETWORK_CONFIG_SECTION.value,
                    self.resource.NetworkConfigSection)
        raise EntityNotFoundException(
            'Can\'t find network \'%s\'' % network_name)

    def add_ip_range(self, network_name, start_ip, end_ip):
        """Add IP range to vApp network.

        :param str network_name: name of vApp network.
        :param str start_ip: start IP of IP range.
        :param str end_ip: last IP of IP range.
        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is updating the vApp network.
        :rtype: lxml.objectify.ObjectifiedElement
        """
        for network_config in self.resource.NetworkConfigSection.NetworkConfig:
            if network_config.get("networkName") == network_name:
                iprange = E.IpRange(
                    E.StartAddress(start_ip), E.EndAddress(end_ip))
                IpScope = network_config.Configuration.IpScopes.IpScope
                if hasattr(IpScope, 'IpRanges'):
                    IpScope.IpRanges.append(iprange)
                else:
                    IpScope.append(E.IpRanges(iprange))
                return self.client.put_linked_resource(
                    self.resource.NetworkConfigSection, RelationType.EDIT,
                    EntityType.NETWORK_CONFIG_SECTION.value,
                    self.resource.NetworkConfigSection)
        raise EntityNotFoundException(
            'Can\'t find network \'%s\'' % network_name)

    def update_ip_range(self, network_name, start_ip, end_ip, new_start_ip,
                        new_end_ip):
        """Update IP range to vApp network.

        :param str network_name: name of vApp network.
        :param str start_ip: start IP of IP range.
        :param str end_ip: last IP of IP range.
        :param str new_start_ip: start IP of IP range to be updated.
        :param str new_end_ip: last IP of IP range to be updated.
        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is updating the vApp network.
        :rtype: lxml.objectify.ObjectifiedElement
        """
        for network_config in self.resource.NetworkConfigSection.NetworkConfig:
            if network_config.get("networkName") == network_name:
                IpScope = network_config.Configuration.IpScopes.IpScope
                if (hasattr(IpScope, 'IpRanges')):
                    for ip_range in IpScope.IpRanges.IpRange:
                        if ip_range.StartAddress == start_ip \
                                and ip_range.EndAddress == end_ip:
                            ip_range.clear()
                            ip_range.append(E.StartAddress(new_start_ip))
                            ip_range.append(E.EndAddress(new_end_ip))
                            return self.client.put_linked_resource(
                                self.resource.NetworkConfigSection,
                                RelationType.EDIT,
                                EntityType.NETWORK_CONFIG_SECTION.value,
                                self.resource.NetworkConfigSection)
                break
        raise EntityNotFoundException(
            'Can\'t find ip range from \'%s\' to \'%s\'' % start_ip, end_ip)

    def delete_ip_range(self, network_name, start_ip, end_ip):
        """Delete IP range to vApp network.

        :param str network_name: name of vApp network.
        :param str start_ip: start IP of IP range.
        :param str end_ip: last IP of IP range.
        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is updating the vApp network.
        :rtype: lxml.objectify.ObjectifiedElement
        """
        for network_config in self.resource.NetworkConfigSection.NetworkConfig:
            if network_config.get("networkName") == network_name:
                IpScope = network_config.Configuration.IpScopes.IpScope
                if (hasattr(IpScope, 'IpRanges')):
                    for ip_range in IpScope.IpRanges.IpRange:
                        if ip_range.StartAddress == start_ip \
                                and ip_range.EndAddress == end_ip:
                            IpScope.IpRanges.remove(ip_range)
                            return self.client.put_linked_resource(
                                self.resource.NetworkConfigSection,
                                RelationType.EDIT,
                                EntityType.NETWORK_CONFIG_SECTION.value,
                                self.resource.NetworkConfigSection)
                break
        raise EntityNotFoundException(
            'Can\'t find IP range from \'%s\' to \'%s\'' % start_ip, end_ip)

    def update_dns_detail(self, ip_scope, type, value):
        """Update DNS details to IpScope.

        :param Element IpScope: parent element.
        :param str type: type is tag.
        :param str value: value of tag.
        """
        if value is None:
            return
        element = etree.Element(type)
        element.text = value
        if hasattr(ip_scope, type):
            ip_scope.remove(ip_scope[type])
        ip_scope.insert(ip_scope.index(ip_scope.IsEnabled), element)

    def update_dns_vapp_network(self,
                                network_name,
                                primary_dns_ip=None,
                                secondary_dns_ip=None,
                                dns_suffix=None):
        """Add DNS details to vApp network.

        :param str network_name: name of App network.
        :param str primary_dns_ip: primary DNS IP.
        :param str secondary_dns_ip: secondary DNS IP.
        :param str dns_suffix: DNS suffix.
        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is updating the vApp network.
        :rtype: lxml.objectify.ObjectifiedElement
        """
        for network_config in self.resource.NetworkConfigSection.NetworkConfig:
            if network_config.get('networkName') == network_name:
                ip_scope = network_config.Configuration.IpScopes.IpScope
                self.update_dns_detail(ip_scope, 'Dns1', primary_dns_ip)
                self.update_dns_detail(ip_scope, 'Dns2', secondary_dns_ip)
                self.update_dns_detail(ip_scope, 'DnsSuffix', dns_suffix)
                return self.client.put_linked_resource(
                    self.resource.NetworkConfigSection, RelationType.EDIT,
                    EntityType.NETWORK_CONFIG_SECTION.value,
                    self.resource.NetworkConfigSection)
        raise EntityNotFoundException(
            'Can\'t find network \'%s\'' % network_name)

    def dns_detail_of_vapp_network(self, network_name):
        """DNS details of vApp network.

        :param str network_name: name of App network.
        :return:  Dictionary having Dns1, Dns2 and DnsSuffix.
        e.g.
        {'Dns1': '10.1.1.1', 'Dns2': '10.1.1.2', 'DnsSuffix':'example.com'}
        :rtype: dict
        :raises: Exception: if the network can't be found.
        """
        for network_config in self.resource.NetworkConfigSection.NetworkConfig:
            if network_config.get('networkName') == network_name:
                ip_scope = network_config.Configuration.IpScopes.IpScope
                dns_details = {}
                if hasattr(ip_scope, 'Dns1'):
                    dns_details['Dns1'] = ip_scope.Dns1
                if hasattr(ip_scope, 'Dns2'):
                    dns_details['Dns2'] = ip_scope.Dns2
                if hasattr(ip_scope, 'DnsSuffix'):
                    dns_details['DnsSuffix'] = ip_scope.DnsSuffix
                return dns_details
        raise EntityNotFoundException(
            'Can\'t find network \'%s\'' % network_name)

    def list_ip_allocations(self, network_name):
        """List all allocated ip of vApp network.

        :param str network_name: name of vApp network.
        :return: list of IP allocation details.
        e.g.
        [{'Allocation_type':'vsmAllocated','Is_deployed':True,
         'Ip_address':'10.1.2.1'},
         {'Allocation_type':'vmAllocated','Is_deployed': True,
         'Ip_address':'10.1.2.12'}]
        :rtype: list.
        """
        self.get_resource()
        vapp_network_resource_href = find_link(
            self.resource,
            rel=RelationType.DOWN,
            media_type=EntityType.vApp_Network.value,
            name=network_name).href
        vapp_network_resource = self.client.get_resource(
            vapp_network_resource_href)
        obj = self.client.get_linked_resource(
            vapp_network_resource, RelationType.DOWN,
            EntityType.ALLOCATED_NETWORK_ADDRESS.value)
        list_allocated_ip = []
        if hasattr(obj, 'IpAddress'):
            for ip_address in obj.IpAddress:
                dict = {}
                dict['Allocation_type'] = ip_address.get('allocationType')
                dict['Is_deployed'] = ip_address.get('isDeployed')
                if hasattr(ip_address, 'IpAddress'):
                    dict['Ip_address'] = ip_address.IpAddress
                list_allocated_ip.append(dict)
        return list_allocated_ip

    def edit_name_and_description(self, name, description=None):
        """Edit name and description of the vApp.

        :param str name: New name of the vApp. It is mandatory.
        :param str description: New description of the vApp.

        :return: object containing EntityType.TASK XML data
            representing the asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if name is None or name.isspace():
            raise InvalidParameterException("Name can't be None or empty")
        vapp = self.get_resource()
        vapp.set('name', name.strip())
        if description is not None:
            if hasattr(vapp, 'Description'):
                vapp.replace(vapp.Description, E.Description(description))
            else:
                vapp.LeaseSettingsSection.addprevious(
                    E.Description(description))

        return self.client.put_linked_resource(
            self.resource, RelationType.EDIT, EntityType.VAPP.value, vapp)

    def suspend_vapp(self):
        """Suspend a vApp.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is suspending the vApp.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        self.get_resource()
        return self.client.post_linked_resource(
            self.resource, RelationType.POWER_SUSPEND, None, None)

    def discard_suspended_state_vapp(self):
        """Discard suspended state of the vApp.

        :return: an object containing EntityType.TASK XML data which represents
                    the asynchronous task that is discarding suspended state
                    of vApp.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        self.get_resource()
        return self.client.post_linked_resource(
            self.resource, RelationType.DISCARD_SUSPENDED_STATE, None, None)

    def enter_maintenance_mode(self):
        """Enter maintenance mode a vApp."""
        self.get_resource()
        return self.client.post_linked_resource(
            self.resource, RelationType.ENTER_MAINTENANCE_MODE, None, None)

    def exit_maintenance_mode(self):
        """Exit maintenance mode a vApp."""
        self.get_resource()
        return self.client.post_linked_resource(
            self.resource, RelationType.EXIT_MAINTENANCE_MODE, None, None)

    def enable_download(self):
        """Helper method to enable an entity for download.

        Behind the scene it involves vCD copying the template/media file
        from ESX hosts to spool area (transfer folder).
        """
        self.get_resource()
        task = self.client.post_linked_resource(
            self.resource, RelationType.ENABLE, None, None)
        self.client.get_task_monitor().wait_for_success(task, 60, 1)

    def disable_download(self):
        """Method to disbale an entity for download."""
        self.get_resource()
        self.client.post_linked_resource(self.resource, RelationType.DISABLE,
                                         None, None)

    def download_ova(self, file_name, chunk_size=DEFAULT_CHUNK_SIZE):
        """Downloads a vapp into a local file.

        :param str file_name: name of the target file on local disk where the
            contents of the vapp will be downloaded to.
        :param int chunk_size: size of chunks in which the vapp will
            be downloaded and written to the disk.

        :return: number of bytes written to file.
        :rtype: int
        """
        self.enable_download()
        self.resource = None
        self.get_resource()
        ova_uri = find_link(self.resource, RelationType.DOWNLOAD_OVA_DEFAULT,
                            EntityType.APPLICATION_BINARY.value).href
        return self.client.download_from_uri(ova_uri, file_name, chunk_size)

    def upgrade_virtual_hardware(self):
        """Upgrade virtual hardware of vapp.

        Behind the scene it upgrades virtual hardware of all the vm belongs to
            vapp.

        :return: no of vm upgraded.
        :rtype: int
        """
        self.resource = None
        self.get_resource()
        no_of_vm_upgraded = 0
        for vm in self.get_all_vms():
            vm_obj = VM(self.client, resource=vm)
            try:
                task = vm_obj.upgrade_virtual_hardware()
                self.client.get_task_monitor().wait_for_success(task)
                no_of_vm_upgraded += 1
            except OperationNotSupportedException:
                LOGGER.error('Operation not supported  for vm ' +
                             vm.get('name'))
        return no_of_vm_upgraded

    def vapp_clone(self, vdc_href, vapp_name, description, source_delete):
        """Copy a vapp to vdc with given name.

        :param str vdc_href: link of vdc where vapp is going to copy.
        :param str vapp_name: name of vapp.
        :param str description: description of vapp.
        :param bool source_delete: if source_delete is true it will delete
            source vapp.
        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is copying the vApp.
        :rtype: lxml.objectify.ObjectifiedElement
        """
        resource = E.CloneVAppParams(name=vapp_name)
        if description is not None:
            resource.append(E.Description(description))
        resource.append(E.Source(href=self.resource.get('href')))
        if source_delete:
            resource.append(E.IsSourceDelete(True))
        else:
            resource.append(E.IsSourceDelete(False))
        for vm in self.get_all_vms():
            sourced_vm_instantiation_params = E.SourcedVmInstantiationParams()
            sourced_vm_instantiation_params.append(
                E.Source(href=vm.get('href')))
            sourced_vm_instantiation_params.append(
                E.StorageProfile(href=vm.StorageProfile.get('href')))
            resource.append(sourced_vm_instantiation_params)
        vdc_resource = self.client.get_resource(vdc_href)
        result = self.client.post_linked_resource(
            vdc_resource, RelationType.ADD, EntityType.CLONE_VAPP_PARAMS.value,
            resource)
        return result.Tasks.Task[0]

    def copy_to(self, vdc_href, vapp_new_name, description):
        """Copy a vapp to vdc with given name.

        :param str vdc_href: link of vdc where vapp is going to copy.
        :param str vapp_new_name: name of vapp.
        :param str description: description of vapp.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is copying the vApp.
        :rtype: lxml.objectify.ObjectifiedElement
        """
        return self.vapp_clone(vdc_href, vapp_new_name, description, False)

    def move_to(self, vdc_href):
        """Move a vapp to another vdc.

        :param str vdc_href: link of vdc where vapp is going to move.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is moving the vApp.
        :rtype: lxml.objectify.ObjectifiedElement
        """
        vapp_name = self.resource.get('name')
        return self.vapp_clone(vdc_href, vapp_name, None, True)

    def create_snapshot(self, memory=False, quiesce=False):
        """Create snapshot of vapp.

        :param bool memory: True, if the snapshot should include the virtual
            machine's memory.
        :param bool quiesce: True, if the file system of the virtual machine
            should be quiesced before the snapshot is created. Requires VMware
            tools to be installed on the vm.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is moving the vApp.
        :rtype: lxml.objectify.ObjectifiedElement
        """
        snapshot_vapp_params = E.CreateSnapshotParams()
        snapshot_vapp_params.set('memory', str(memory).lower())
        snapshot_vapp_params.set('quiesce', str(quiesce).lower())
        return self.client.post_linked_resource(
            self.resource, RelationType.SNAPSHOT_CREATE,
            EntityType.SNAPSHOT_CREATE.value, snapshot_vapp_params)

    def snapshot_revert_to_current(self):
        """Reverts a vapp to the current snapshot, if any.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is reverting the snapshot.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        self.get_resource()
        return self.client.post_linked_resource(
            self.resource, RelationType.SNAPSHOT_REVERT_TO_CURRENT, None, None)

    def snapshot_remove(self):
        """Remove snapshots of a vapp.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task removing the snapshots.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        self.get_resource()
        return self.client.post_linked_resource(
            self.resource, RelationType.SNAPSHOT_REMOVE_ALL, None, None)

    def get_vapp_network_list(self):
        """Returns the list of vapp network defined in the vApp.

        :return: list of the vapp network name.

        :rtype: list
        """
        self.get_resource()
        vapp_network_list = []
        for network_config in self.resource.NetworkConfigSection.NetworkConfig:
            if network_config.get('networkName') != 'none':
                vapp_network_list.append({
                    'name':
                    network_config.get('networkName')
                })
        return vapp_network_list

    def sync_syslog_settings(self, network_name):
        """Sync syslog settings of vApp network.

        :param str network_name: name of App network.
        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is updating the vApp network.
        :rtype: lxml.objectify.ObjectifiedElement
        :raises: Exception: if the network can't be found.
        """
        for network_config in self.resource.NetworkConfigSection.NetworkConfig:
            if network_config.get('networkName') == network_name:
                return self.client.post_linked_resource(
                    resource=network_config,
                    rel=RelationType.SYNC_SYSLOG_SETTINGS,
                    media_type=EntityType.TASK.value,
                    contents=None)
        raise EntityNotFoundException(
            'Can\'t find network \'%s\'' % network_name)

    def connect_vapp_network_to_ovdc_network(self, network_name,
                                             orgvdc_network_name):
        """Connect vapp network to org vdc network.

        :param str network_name: name of App network.
        :param str orgvdc_network_name: org vdc network name.
        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is updating the vApp network.
        :rtype: lxml.objectify.ObjectifiedElement
        """
        vdc = VDC(
            self.client,
            href=find_link(self.resource, RelationType.UP,
                           EntityType.VDC.value).href)
        orgvdc_network_href = vdc.get_orgvdc_network_admin_href_by_name(
            orgvdc_network_name)
        ovdc_net_res = self.client.get_resource(orgvdc_network_href)
        vapp_network_href = find_link(
            resource=self.resource,
            rel=RelationType.DOWN,
            media_type=EntityType.vApp_Network.value,
            name=network_name).href
        vapp_net_res = self.client.get_resource(vapp_network_href)
        parent_network = E.ParentNetwork()
        parent_network.set('href', orgvdc_network_href)
        parent_network.set('id', ovdc_net_res.get('id'))
        parent_network.set('name', ovdc_net_res.get('name'))
        vapp_net_res.Configuration.FenceMode.addprevious(parent_network)
        vapp_net_res.Configuration.remove(vapp_net_res.Configuration.FenceMode)
        vapp_net_res.Configuration.ParentNetwork.addnext(
            E.FenceMode(FenceMode.NAT_ROUTED.value))
        return self.client.put_linked_resource(
            resource=vapp_net_res,
            rel=RelationType.EDIT,
            media_type=EntityType.vApp_Network.value,
            contents=vapp_net_res)

    def create_vapp_network_from_ovdc_network(self, orgvdc_network_name):
        """Create vapp network from org vdc network.

        :param str orgvdc_network_name: org vdc network name.
        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is updating the vApp network.
        :rtype: lxml.objectify.ObjectifiedElement
        """
        vdc = VDC(
            self.client,
            href=find_link(self.resource, RelationType.UP,
                           EntityType.VDC.value).href)
        orgvdc_network_href = vdc.get_orgvdc_network_admin_href_by_name(
            orgvdc_network_name)
        ovdc_net_res = self.client.get_resource(orgvdc_network_href)
        res_ip_scope = ovdc_net_res.Configuration.IpScopes.IpScope

        self.get_resource()
        network_config_section = \
            deepcopy(self.resource.NetworkConfigSection)
        network_config = E.NetworkConfig(networkName=orgvdc_network_name)

        config = E.Configuration()
        ip_scopes = E.IpScopes()
        ip_scope = E.IpScope()

        ip_scope.append(E.IsInherited(True))
        ip_scope.append(res_ip_scope.Gateway)
        ip_scope.append(res_ip_scope.SubnetPrefixLength)
        if hasattr(res_ip_scope, 'Dns1'):
            ip_scope.append(res_ip_scope.Dns1)
        if hasattr(res_ip_scope, 'Dns2'):
            ip_scope.append(res_ip_scope.Dns2)
        if hasattr(res_ip_scope, 'DnsSuffix'):
            ip_scope.append(res_ip_scope.DnsSuffix)
        if hasattr(res_ip_scope, 'IsEnabled'):
            ip_scope.append(res_ip_scope.IsEnabled)
        ip_scopes.append(ip_scope)
        config.append(ip_scopes)
        parent_network = E.ParentNetwork()
        parent_network.set('href', orgvdc_network_href)
        parent_network.set('id', ovdc_net_res.get('id'))
        parent_network.set('name', ovdc_net_res.get('name'))
        config.append(parent_network)
        config.append(E.FenceMode(FenceMode.BRIDGED.value))
        config.append(E.AdvancedNetworkingEnabled(True))
        network_config.append(config)
        network_config.append(E.IsDeployed(False))
        network_config_section.append(network_config)
        return self.client.put_linked_resource(
            self.resource.NetworkConfigSection, RelationType.EDIT,
            EntityType.NETWORK_CONFIG_SECTION.value, network_config_section)

    def enable_fence_mode(self):
        """Enable fence mode of vapp network.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is updating the vApp network.
        :rtype: lxml.objectify.ObjectifiedElement
        """
        self.get_resource()
        network_config_section = deepcopy(self.resource.NetworkConfigSection)
        for network_config in network_config_section.NetworkConfig:
            if network_config.Configuration.IpScopes.IpScope.IsInherited:
                network_config.Configuration.remove(
                    network_config.Configuration.FenceMode)
                network_config.Configuration.ParentNetwork.addnext(
                    E.FenceMode(FenceMode.NAT_ROUTED.value))
                features = E.Features()
                firewall_services = E.FirewallService()
                firewall_services.append(E.IsEnabled(True))
                firewall_services.append(E.DefaultAction('drop'))
                firewall_services.append(E.LogDefaultAction(False))
                firewall_rule = E.FirewallRule()
                firewall_rule.append(E.IsEnabled(True))
                firewall_rule.append(
                    E.Description('Allow all outgoing traffic'))
                firewall_rule.append(E.Policy('allow'))
                protocol = E.Protocols()
                protocol.append(E.Any(True))
                firewall_rule.append(protocol)
                firewall_rule.append(E.DestinationPortRange('Any'))
                firewall_rule.append(E.DestinationIp('external'))
                firewall_rule.append(E.SourcePortRange('Any'))
                firewall_rule.append(E.SourceIp('internal'))
                firewall_rule.append(E.EnableLogging(False))
                firewall_services.append(firewall_rule)
                features.append(firewall_services)
        return self.client.put_linked_resource(
            self.resource.NetworkConfigSection, RelationType.EDIT,
            EntityType.NETWORK_CONFIG_SECTION.value, network_config_section)

    def update_startup_section(self,
                               vm_name,
                               order=None,
                               start_action=None,
                               start_delay=None,
                               stop_action=None,
                               stop_delay=None):
        """Update startup section of vapp.

        :param str vm_name: name of VM in App.
        :param int order: start order of vm.
        :param str start_action: action on VM on start of App.
        :param int start_delay: start delay of vm.
        :param str stop_action: action on VM on stop of App.
        :param int stop_delay: stop delay of vm.
        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is updating the vApp startup section.
        :rtype: lxml.objectify.ObjectifiedElement
        """
        startup_section = self.resource.xpath(
            'ovf:StartupSection', namespaces=NSMAP)
        startup_section_href = startup_section[0].get('{' + NSMAP['ns10'] +
                                                      '}href')
        startup_section_res = self.client.get_resource(startup_section_href)
        items = startup_section_res.xpath('ovf:Item', namespaces=NSMAP)
        for item in items:
            if item.get('{' + NSMAP['ovf'] + '}id') == vm_name:
                if order is not None:
                    item.set('{' + NSMAP['ovf'] + '}order', str(order))
                if start_action is not None:
                    item.set('{' + NSMAP['ovf'] + '}startAction', start_action)
                if start_delay is not None:
                    item.set('{' + NSMAP['ovf'] + '}startDelay',
                             str(start_delay))
                if stop_action is not None:
                    item.set('{' + NSMAP['ovf'] + '}stopAction', stop_action)
                if stop_delay is not None:
                    item.set('{' + NSMAP['ovf'] + '}stopDelay',
                             str(stop_delay))
        return self.client.put_linked_resource(
            startup_section_res,
            rel=RelationType.EDIT,
            media_type=EntityType.STARTUP_SECTION.value,
            contents=startup_section_res)

    def get_startup_section(self):
        """Get startup section data of vapp.

        :return: a list of dictionary containing startup sections Data of the
            vApp.

        :rtype: list
        """
        startup_section = self.resource.xpath(
            'ovf:StartupSection', namespaces=NSMAP)
        items = startup_section[0].xpath('ovf:Item', namespaces=NSMAP)
        startup_section_info = []
        for item in items:
            item_detail = {}
            item_detail['Id'] = item.get('{' + NSMAP['ovf'] + '}id')
            item_detail['order'] = item.get('{' + NSMAP['ovf'] + '}order')
            item_detail['startAction'] = item.get('{' + NSMAP['ovf'] +
                                                  '}startAction')
            item_detail['startDelay'] = item.get('{' + NSMAP['ovf'] +
                                                 '}startDelay')
            item_detail['stopAction'] = item.get('{' + NSMAP['ovf'] +
                                                 '}stopAction')
            item_detail['stopDelay'] = item.get('{' + NSMAP['ovf'] +
                                                '}stopDelay')
            startup_section_info.append(item_detail)
        return startup_section_info

    def get_product_sections(self):
        """Get product sections data of vapp.

        :return: a list containing dictionary of product sections Data of the
            vApp.

        :rtype: list
        """
        self.get_resource()
        product_sections_res = self.client.get_linked_resource(
            self.resource, RelationType.DOWN,
            EntityType.PRODUCT_SECTIONS.value)
        product_sections = product_sections_res.xpath(
            'ovf:ProductSection', namespaces=NSMAP)
        product_sections_info = []
        for product_section in product_sections:
            product_section_info = {}
            product_section_info['info'] = product_section.Info
            properties = product_section.xpath(
                'ovf:Property', namespaces=NSMAP)
            for property in properties:
                product_section_info[property.get(
                    '{' + NSMAP['ovf'] +
                    '}key')] = property.get('{' + NSMAP['ovf'] + '}value')
            product_sections_info.append(product_section_info)
        return product_sections_info

    def update_product_section(self,
                               key,
                               type='string',
                               class_name='',
                               instance_name='',
                               value='',
                               label=None,
                               is_password=False,
                               user_configurable=False):
        """Update product section of vapp.

        :param str key: key for property in product section of App.
        :param str type: value type for property in product section of App.
        :param str class_name: class name for product section of vapp.
        :param str instance_name: instance name for product section of vapp.
        :param str value: value for property in product section of App.
        :param str label: label for property in product section of App.
        :param str is_password: value for property is password or not in
            product section of App.
        :param str user_configurable: value for property is user configurable
            or not in product section of App.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is updating the vApp product section.
        :rtype: lxml.objectify.ObjectifiedElement
        """
        property = E_OVF.Property()
        property.set('{' + NSMAP['ovf'] + '}key', key)
        if is_password:
            property.set('{' + NSMAP['ovf'] + '}password', 'true')
        else:
            property.set('{' + NSMAP['ovf'] + '}password', 'false')
        property.set('{' + NSMAP['ovf'] + '}type', type)
        if user_configurable:
            property.set('{' + NSMAP['ovf'] + '}userConfigurable', 'true')
        else:
            property.set('{' + NSMAP['ovf'] + '}userConfigurable', 'false')
        property.set('{' + NSMAP['ovf'] + '}value', str(value))
        if label is not None:
            property.append(E_OVF.Label(label))
        self.get_resource()
        product_sections_res = self.client.get_linked_resource(
            self.resource, RelationType.DOWN,
            EntityType.PRODUCT_SECTIONS.value)
        product_sections = product_sections_res.xpath(
            'ovf:ProductSection', namespaces=NSMAP)
        is_updated = False
        for product_section in product_sections:
            class_val = product_section.get('{' + NSMAP['ovf'] + '}class')
            instance_val = product_section.get('{' + NSMAP['ovf'] +
                                               '}instance')
            if class_name == class_val and instance_name == instance_val:
                properties = product_section.xpath(
                    'ovf:Property', namespaces=NSMAP)
                for prop in properties:
                    id = prop.get('{' + NSMAP['ovf'] + '}key')
                    if key == id:
                        prop.getparent().remove(prop)
                product_section.append(property)
                is_updated = True
                break
        if not is_updated:
            product_section = E_OVF.ProductSection()
            if class_name is not None:
                product_section.set('{' + NSMAP['ovf'] + '}class', class_name)
            if instance_name is not None:
                product_section.set('{' + NSMAP['ovf'] + '}instance',
                                    instance_name)
            info = E_OVF.Info()
            product_section.append(info)
            product_section.append(property)
            product_sections_res.append(product_section)
        return self.client.put_linked_resource(
            product_sections_res,
            rel=RelationType.EDIT,
            media_type=EntityType.PRODUCT_SECTIONS.value,
            contents=product_sections_res)

    def list_vm_interface(self, network_name):
        """List vm interfaces of network.

        :param str network_name: name of network.

        :return: a list of dictionary that contain list of interfaces.
        :rtype: list
        """
        self.get_resource()
        result = []
        if hasattr(self.resource, 'Children') and \
                hasattr(self.resource.Children, 'Vm'):
            for vm in self.resource.Children.Vm:
                local_id = vm.VAppScopedLocalId
                if hasattr(vm, 'NetworkConnectionSection'):
                    net_con_section = vm.NetworkConnectionSection
                    if hasattr(net_con_section, 'NetworkConnection'):
                        net_con = net_con_section.NetworkConnection
                        for network_connection in net_con:
                            vm_interface_data = {}
                            if network_connection.get(
                                    'network') == network_name:
                                vm_interface_data['Name'] = network_name
                                vm_interface_data['Local_id'] = local_id
                                vm_interface_data['VmNicId'] = \
                                    network_connection.NetworkConnectionIndex
                                result.append(vm_interface_data)
        return result

    def add_vm_from_scratch(self,
                            specs,
                            deploy=True,
                            power_on=True,
                            all_eulas_accepted=True):
        """Recompose the vApp and add vm.

        :param dict specs: vm specifications, see `to_vm_item()` method
            for specification details.
        :param bool deploy: True, if the vApp should be deployed at
            instantiation.
        :param power_on: (bool): True if the vApp should be powered-on at
            instantiation
        :param bool all_eulas_accepted: True confirms acceptance of all
            EULAs in the vApp.

        :return: an object containing EntityType.VAPP XML data representing the
            updated vApp.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        params = E.RecomposeVAppParams(deploy='true' if deploy else 'false',
                                       powerOn='true' if power_on else 'false')
        params.append(self.to_vm_item(specs))
        params.append(E.AllEULAsAccepted(all_eulas_accepted))
        return self.client.post_linked_resource(
            self.resource, RelationType.RECOMPOSE,
            EntityType.RECOMPOSE_VAPP_PARAMS.value, params)

    def to_vm_item(self, specs):
        """Creates a vm CreateItem from a vm specification.

        :param dict specs: a dictionary containing
            - vm_name: (str): (required) vm name.
            - comp_name: (str): (required) computer name.
            - description: (str): (optional) description of the vm.
            - os_type: (str): (required) operating system type of vm.
            - virtual_cpu: (int): (optional) no of virtual cpu.
            - core_per_socket: (int):(optional) core per socket in cpu.
            - cpu_resource_mhz: (int):(optional) cpu resource frequency in Mhz
            - memory: (int):(optional) memory in Mb.
            - media_href: (str): (optional) boot image of os href.
            - media_id: (str): (optional) c boot image of os id.
            - media_name: (str): (optional)  boot image of os name.

        :return: an object containing CreateItem XML element.
        :rtype: lxml.objectify.ObjectifiedElement
        """
        create_item = E.CreateItem()
        create_item.set('name', specs['vm_name'])
        desc = E.Description()
        if 'description' in specs:
            desc = E.Description(specs['description'])
        create_item.append(desc)
        guest_customization_param = E.GuestCustomizationSection()
        guest_customization_param.append(
            E_OVF.Info('Specifies Guest OS Customization Settings'))
        guest_customization_param.append(E.ComputerName(specs['comp_name']))
        create_item.append(guest_customization_param)
        vm_spec_section = E.VmSpecSection()
        vm_spec_section.set('Modified', 'true')
        vm_spec_section.append(E_OVF.Info('Virtual Machine specification'))
        vm_spec_section.append(E.OsType(specs['os_type']))
        if 'virtual_cpu' in specs:
            vm_spec_section.append(E.NumCpus(specs['virtual_cpu']))
        else:
            vm_spec_section.append(E.NumCpus(1))
        if 'core_per_socket' in specs:
            vm_spec_section.append(
                E.NumCoresPerSocket(specs['core_per_socket']))
        else:
            vm_spec_section.append(E.NumCoresPerSocket(1))
        cpu_resource_mhz = E.CpuResourceMhz()
        if 'cpu_resource_mhz' in specs:
            cpu_resource_mhz.append(E.Configured(specs['cpu_resource_mhz']))
        else:
            cpu_resource_mhz.append(E.Configured(0))
        vm_spec_section.append(cpu_resource_mhz)
        memory_resource_mb = E.MemoryResourceMb()
        if 'memory' in specs:
            memory_resource_mb.append(E.Configured(specs['memory']))
        else:
            memory_resource_mb.append(E.Configured(512))
        vm_spec_section.append(memory_resource_mb)
        vm_spec_section.append(E.DiskSection())
        vm_spec_section.append(E.HardwareVersion('vmx-14'))
        vm_spec_section.append(E.VirtualCpuType('VM64'))
        create_item.append(vm_spec_section)
        if 'media_href' in specs and 'media_id' in specs and 'media_name' in \
                specs:
            media = E.Media()
            media.set('href', specs['media_href'])
            media.set('id', specs['media_id'])
            media.set('name', specs['media_name'])
            create_item.append(media)
        return create_item
