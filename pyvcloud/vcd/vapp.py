# VMware vCloud Director Python SDK
# Copyright (c) 2014 VMware, Inc. All Rights Reserved.
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
from pyvcloud.vcd.client import E
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import RelationType


class VApp(object):

    def __init__(self, client, name=None, href=None, resource=None):
        self.client = client
        self.name = name
        self.href = href
        self.resource = resource
        if resource is not None:
            self.name = resource.get('name')
            self.href = resource.get('href')

    def reload(self):
        self.resource = self.client.get_resource(self.href)
        if self.resource is not None:
            self.name = self.resource.get('name')
            self.href = self.resource.get('href')

    def get_primary_ip(self, vm_name):
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        if hasattr(self.resource, 'Children') and \
           hasattr(self.resource.Children, 'Vm'):
            for vm in self.resource.Children.Vm:
                if vm_name == vm.get('name'):
                    items = vm.xpath(
                        '//ovf:VirtualHardwareSection/ovf:Item',
                        namespaces=NSMAP)
                    for item in items:
                        connection = item.find('rasd:Connection', NSMAP)
                        if connection is not None:
                            return connection.get('{http://www.vmware.com/vcloud/v1.5}ipAddress')  # NOQA
        raise Exception('can\'t find ip address')

    def get_admin_password(self, vm_name):
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        if hasattr(self.resource, 'Children') and \
           hasattr(self.resource.Children, 'Vm'):
            for vm in self.resource.Children.Vm:
                if vm_name == vm.get('name'):
                    if hasattr(vm, 'GuestCustomizationSection') and \
                       hasattr(vm.GuestCustomizationSection, 'AdminPassword'):
                        return vm.GuestCustomizationSection.AdminPassword.text
        raise Exception('can\'t find admin password')

    def get_metadata(self):
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        return self.client.get_linked_resource(self.resource,
                                               RelationType.DOWN,
                                               EntityType.METADATA.value)

    def set_metadata(self,
                     domain,
                     visibility,
                     key,
                     value,
                     metadata_type='MetadataStringValue'):
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        new_metadata = E.Metadata(
            E.MetadataEntry(
                {'type': 'xs:string'},
                E.Domain(domain, visibility=visibility),
                E.Key(key),
                E.TypedValue(
                    {'{http://www.w3.org/2001/XMLSchema-instance}type':
                     'MetadataStringValue'},
                    E.Value(value))))
        metadata = self.client.get_linked_resource(self.resource,
                                                   RelationType.DOWN,
                                                   EntityType.METADATA.value)
        return self.client.post_linked_resource(metadata,
                                                RelationType.ADD,
                                                EntityType.METADATA.value,
                                                new_metadata)

    def get_vm_moid(self, vm_name):
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        vapp = self.resource
        if hasattr(vapp, 'Children') and hasattr(vapp.Children, 'Vm'):
            for vm in vapp.Children.Vm:
                if vm.get('name') == vm_name:
                    env = vm.xpath('//ovfenv:Environment', namespaces=NSMAP)
                    if len(env) > 0:
                        return env[0].get('{http://www.vmware.com/schema/ovfenv}vCenterId')  # NOQA
        return None

    def set_lease(self, deployment_lease=0, storage_lease=0):
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        new_section = self.resource.LeaseSettingsSection

        new_section.DeploymentLeaseInSeconds = deployment_lease
        new_section.StorageLeaseInSeconds = storage_lease
        objectify.deannotate(new_section)
        etree.cleanup_namespaces(new_section)
        return self.client.put_resource(
            self.resource.get('href') + '/leaseSettingsSection/',
            new_section,
            EntityType.LEASE_SETTINGS.value)

    def change_owner(self, href):
        """
        Change the ownership of vApp to a given user.
        :param href: Href of the new owner or user.
        :return: None.
        """ # NOQA
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        new_owner = self.resource.Owner
        new_owner.User.set('href', href)
        objectify.deannotate(new_owner)
        etree.cleanup_namespaces(new_owner)
        return self.client.put_resource(
            self.resource.get('href') + '/owner/',
            new_owner,
            EntityType.OWNER.value)

    def power_off(self):
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        return self.client.post_linked_resource(
            self.resource,
            RelationType.POWER_OFF,
            None,
            None)

    def power_on(self):
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        return self.client.post_linked_resource(
            self.resource,
            RelationType.POWER_ON,
            None,
            None)

    def shutdown(self):
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        return self.client.post_linked_resource(
            self.resource,
            RelationType.POWER_SHUTDOWN,
            None,
            None)

    def connect_vm(self, mode='DHCP', reset_mac_address=False):
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        if hasattr(self.resource, 'Children') and \
           hasattr(self.resource.Children, 'Vm') and \
           len(self.resource.Children.Vm) > 0:
            network_name = 'none'
            for nc in self.resource.NetworkConfigSection.NetworkConfig:
                if nc.get('networkName') != 'none':
                    network_name = nc.get('networkName')
                    break
            self.resource.Children.Vm[0].NetworkConnectionSection.NetworkConnection.set('network', network_name) # NOQA
            self.resource.Children.Vm[0].NetworkConnectionSection.NetworkConnection.IsConnected = E.IsConnected('true') # NOQA
            if reset_mac_address:
                self.resource.Children.Vm[0].NetworkConnectionSection.NetworkConnection.MACAddress = E.MACAddress('') # NOQA
            self.resource.Children.Vm[0].NetworkConnectionSection.NetworkConnection.IpAddressAllocationMode = E.IpAddressAllocationMode(mode.upper()) # NOQA
            return self.client.put_linked_resource(
                self.resource.Children.Vm[0].NetworkConnectionSection,
                RelationType.EDIT,
                EntityType.NETWORK_CONNECTION_SECTION.value,
                self.resource.Children.Vm[0].NetworkConnectionSection
                )

    def attach_disk_to_vm(self, disk_href, disk_type, disk_name, vm_name):
        """
        Attach the independent disk to the VM with the given name in the vApp within a Virtual Data Center.
        :param disk_href: (str): The href of the disk resource.
        :param vm_name: (str): The name of the VM.
        :return: (vmType)  A :class:`lxml.objectify.StringElement` object describing the requested VM.
        """  # NOQA
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        diskAttachOrDetachParams = E.DiskAttachOrDetachParams(
            E.Disk(type=disk_type, href=disk_href))
        vm = self.get_vm(vm_name)
        return self.client.post_linked_resource(
            vm,
            RelationType.DISK_ATTACH,
            EntityType.DISK_ATTACH_DETACH_PARAMS.value,
            diskAttachOrDetachParams)

    def detach_disk_from_vm(self, disk_href, disk_type, disk_name, vm_name):
        """
        Detach the independent disk from the VM with the given name in the vApp within a Virtual Data Center.
        :param disk_href: (str): The href of the disk resource.
        :param vm_name: (str): The name of the VM.
        :return: (vmType)  A :class:`lxml.objectify.StringElement` object describing the requested VM.
        """  # NOQA
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        diskAttachOrDetachParams = E.DiskAttachOrDetachParams(
            E.Disk(type=disk_type, href=disk_href))
        vm = self.get_vm(vm_name)
        return self.client.post_linked_resource(
            vm,
            RelationType.DISK_DETACH,
            EntityType.DISK_ATTACH_DETACH_PARAMS.value,
            diskAttachOrDetachParams)

    def get_vm(self, vm_name):
        """
        Retrieve the VM with the given name in the vApp within a Virtual Data Center.
        :param vm_name: (str): The name of the VM.
        :return: (vmType)  A :class:`lxml.objectify.StringElement` object describing the requested VM.
        """  # NOQA
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        if hasattr(self.resource, 'Children') and \
           hasattr(self.resource.Children, 'Vm') and \
           len(self.resource.Children.Vm) > 0:
                    for vm in self.resource.Children.Vm:
                        if vm.get('name') == vm_name:
                            return vm
        raise Exception('can\'t find VM')

    def add_disk_to_vm(self, vm_name, disk_size):
        """
        Add a virtual disk to a virtual machine in the vApp.
        It assumes that the VM has already at least one virtual hard disk
        and will attempt to create another one with similar characteristics.

        :param vm_name: (str): The name of the vm to be customized.
        :param disk_size: (int): The size of the disk to be added, in MBs.
        :return:  A :class:`lxml.objectify.StringElement` object describing the asynchronous Task creating the disk.

        :raises: Exception: If the named VM cannot be located or another error occured.
        """  # NOQA
        vm = self.get_vm(vm_name)
        disk_list = self.client.get_resource(vm.get('href') + '/virtualHardwareSection/disks')  # NOQA
        last_disk = None
        for disk in disk_list.Item:
            if disk['{' + NSMAP['rasd'] + '}Description'] == 'Hard disk':  # NOQA
                last_disk = disk
        assert last_disk is not None
        new_disk = deepcopy(last_disk)
        addr = int(str(last_disk['{' + NSMAP['rasd'] + '}AddressOnParent'])) + 1  # NOQA
        instance_id = int(str(last_disk['{' + NSMAP['rasd'] + '}InstanceID'])) + 1  # NOQA
        new_disk['{' + NSMAP['rasd'] + '}AddressOnParent'] = addr
        new_disk['{' + NSMAP['rasd'] + '}ElementName'] = 'Hard disk %s' % addr  # NOQA
        new_disk['{' + NSMAP['rasd'] + '}InstanceID'] = instance_id
        new_disk['{' + NSMAP['rasd'] + '}VirtualQuantity'] = disk_size * 1024 * 1024  # NOQA
        new_disk['{' + NSMAP['rasd'] + '}HostResource'].set('{' + NSMAP['vcloud'] + '}capacity', str(disk_size))  # NOQA
        disk_list.append(new_disk)
        return self.client.put_resource(
            vm.get('href') + '/virtualHardwareSection/disks',
            disk_list,
            EntityType.RASD_ITEM_LIST.value)
