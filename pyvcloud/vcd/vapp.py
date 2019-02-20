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
from pyvcloud.vcd.vdc import VDC


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

    def add_disk_to_vm(self, vm_name, disk_size):
        """Add a virtual disk to a virtual machine in the vApp.

        It assumes that the vm has already at least one virtual hard disk
        and will attempt to create another one with similar characteristics.

        :param str vm_name: name of the vm to be customized.
        :param int disk_size: size of the disk to be added, in MBs.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is creating the disk.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: EntityNotFoundException: if the named vm cannot be located.
            occurred.
        """
        vm = self.get_vm(vm_name)
        disk_list = self.client.get_resource(
            vm.get('href') + '/virtualHardwareSection/disks')
        last_disk = None
        for disk in disk_list.Item:
            if disk['{' + NSMAP['rasd'] + '}Description'] == 'Hard disk':
                last_disk = disk
        assert last_disk is not None
        new_disk = deepcopy(last_disk)
        addr = int(str(
            last_disk['{' + NSMAP['rasd'] + '}AddressOnParent'])) + 1
        instance_id = int(str(
            last_disk['{' + NSMAP['rasd'] + '}InstanceID'])) + 1
        new_disk['{' + NSMAP['rasd'] + '}AddressOnParent'] = addr
        new_disk['{' + NSMAP['rasd'] + '}ElementName'] = 'Hard disk %s' % addr
        new_disk['{' + NSMAP['rasd'] + '}InstanceID'] = instance_id
        new_disk['{' + NSMAP['rasd'] + '}VirtualQuantity'] = \
            disk_size * 1024 * 1024
        new_disk['{' + NSMAP['rasd'] + '}HostResource'].set(
            '{' + NSMAP['vcloud'] + '}capacity', str(disk_size))
        disk_list.append(new_disk)
        return self.client.put_resource(
            vm.get('href') + '/virtualHardwareSection/disks', disk_list,
            EntityType.RASD_ITEMS_LIST.value)

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

        return sourced_item

    def add_vms(self,
                specs,
                deploy=True,
                power_on=True,
                all_eulas_accepted=None):
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
