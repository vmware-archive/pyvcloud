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
from pyvcloud.vcd.client import E_OVF
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.utils import access_control_settings_to_dict


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
                        'ovf:VirtualHardwareSection/ovf:Item',
                        namespaces=NSMAP)
                    for item in items:
                        connection = item.find('rasd:Connection', NSMAP)
                        if connection is not None:
                            return connection.get(
                                '{' + NSMAP['vcloud'] + '}ipAddress')
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
        return self.client.get_linked_resource(
            self.resource, RelationType.DOWN, EntityType.METADATA.value)

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
                {
                    'type': 'xs:string'
                }, E.Domain(domain, visibility=visibility), E.Key(key),
                E.TypedValue(
                    {
                        '{' + NSMAP['xsi'] + '}type': 'MetadataStringValue'
                    }, E.Value(value))))
        metadata = self.client.get_linked_resource(
            self.resource, RelationType.DOWN, EntityType.METADATA.value)
        return self.client.post_linked_resource(metadata, RelationType.ADD,
                                                EntityType.METADATA.value,
                                                new_metadata)

    def get_vm_moid(self, vm_name):
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        vapp = self.resource
        if hasattr(vapp, 'Children') and hasattr(vapp.Children, 'Vm'):
            for vm in vapp.Children.Vm:
                if vm.get('name') == vm_name:
                    env = vm.xpath('ovfenv:Environment', namespaces=NSMAP)
                    if len(env) > 0:
                        return env[0].get('{' + NSMAP['ve'] + '}vCenterId')
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
            self.resource.get('href') + '/leaseSettingsSection/', new_section,
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
            self.resource.get('href') + '/owner/', new_owner,
            EntityType.OWNER.value)

    def power_off(self):
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        return self.client.post_linked_resource(
            self.resource, RelationType.POWER_OFF, None, None)

    def power_on(self):
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        return self.client.post_linked_resource(
            self.resource, RelationType.POWER_ON, None, None)

    def shutdown(self):
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        return self.client.post_linked_resource(
            self.resource, RelationType.POWER_SHUTDOWN, None, None)

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
        """
        Attach the independent disk to the VM with the given name in the vApp within a Virtual Data Center.
        :param disk_href: (str): The href of the disk resource.
        :param vm_name: (str): The name of the VM.
        :return: (vmType)  A :class:`lxml.objectify.StringElement` object describing the requested VM.
        """  # NOQA
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        disk_attach_or_detach_params = E.DiskAttachOrDetachParams(
            E.Disk(type=EntityType.DISK.value, href=disk_href))
        vm = self.get_vm(vm_name)
        return self.client.post_linked_resource(
            vm, RelationType.DISK_ATTACH,
            EntityType.DISK_ATTACH_DETACH_PARAMS.value,
            disk_attach_or_detach_params)

    def detach_disk_from_vm(self, disk_href, disk_type, disk_name, vm_name):
        """
        Detach the independent disk from the VM with the given name in the vApp within a Virtual Data Center.
        :param disk_href: (str): The href of the disk resource.
        :param vm_name: (str): The name of the VM.
        :return: (vmType)  A :class:`lxml.objectify.StringElement` object describing the requested VM.
        """  # NOQA
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        disk_attach_or_detach_params = E.DiskAttachOrDetachParams(
            E.Disk(type=disk_type, href=disk_href))
        vm = self.get_vm(vm_name)
        return self.client.post_linked_resource(
            vm, RelationType.DISK_DETACH,
            EntityType.DISK_ATTACH_DETACH_PARAMS.value,
            disk_attach_or_detach_params)

    def get_all_vms(self):
        """Retrieve all the VMs in this vApp.

        :return: ([vmType])  A array of :class:`lxml.objectify.StringElement`
            object describing the requested VMs.
        """

        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        if hasattr(self.resource, 'Children') and \
           hasattr(self.resource.Children, 'Vm') and \
           len(self.resource.Children.Vm) > 0:
            return self.resource.Children.Vm
        else:
            return []

    def get_vm(self, vm_name):
        """Retrieve the VM with the given name in this vApp.

        :param vm_name: (str): The name of the VM.
        :return: (vmType)  A :class:`lxml.objectify.StringElement` object
            describing the requested VM.
        """

        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        for vm in self.get_all_vms():
            if vm.get('name') == vm_name:
                return vm
        raise Exception('Can\'t find VM %s' % vm_name)

    def add_disk_to_vm(self, vm_name, disk_size):
        """Add a virtual disk to a virtual machine in the vApp.

        It assumes that the VM has already at least one virtual hard disk
        and will attempt to create another one with similar characteristics.

        :param vm_name: (str): The name of the vm to be customized.
        :param disk_size: (int): The size of the disk to be added, in MBs.
        :return:  A :class:`lxml.objectify.StringElement` object describing the
            asynchronous Task creating the disk.

        :raises: Exception: If the named VM cannot be located or another error
            occured.
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
        new_disk['{' + NSMAP['rasd'] +
                 '}VirtualQuantity'] = disk_size * 1024 * 1024
        new_disk['{' + NSMAP['rasd'] + '}HostResource'].set(
            '{' + NSMAP['vcloud'] + '}capacity', str(disk_size))
        disk_list.append(new_disk)
        return self.client.put_resource(
            vm.get('href') + '/virtualHardwareSection/disks', disk_list,
            EntityType.RASD_ITEMS_LIST.value)

    def get_access_control_settings(self):
        """Get the access control settings of the vapp.

        :return: (dict): Access control settings of the vapp.
        """

        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        access_control_settings = self.client.get_linked_resource(
            self.resource, RelationType.DOWN,
            EntityType.CONTROL_ACCESS_PARAMS.value)
        return access_control_settings_to_dict(access_control_settings)

    def get_all_networks(self):
        """Helper method that returns the list of networks defined in the vApp.

        :return:  A :class:`lxml.objectify.StringElement` object with the list
            of vApp networks.
        """

        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        return self.resource.xpath(
            '//ovf:NetworkSection/ovf:Network',
            namespaces={
                'ovf': NSMAP['ovf']
            })

    def get_vapp_network_name(self, index=0):
        """Returns the name of the network defined in the vApp by index.

        :param index: (int): The index of the vApp network to retrieve.
            0 if omitted.

        :return:  A :class:`string` with the name of the requested network if
            exists.
        """

        networks = self.get_all_networks()
        if networks is None or len(networks) < index + 1:
            raise Exception('Can\'t find the specified vApp network')
        return networks[index].get('{' + NSMAP['ovf'] + '}name')

    def to_sourced_item(self, spec):
        """Creates a VM SourcedItem from a VM specification.

        :param spec: (dict) containing:
            vapp: (resource): (required) source vApp or vAppTemplate resource
            source_vm_name: (str): (required) source VM name
            target_vm_name: (str): (optional) target VM name
            hostname: (str): (optional) target guest hostname
            password: (str): (optional) set the administrator password of this
                machine to this value
            password_auto: (bool): (optional) autogenerate administrator
                password
            password_reset: (bool): (optional) True if the administrator
                password for this virtual machine must be reset after first use
            cust_script: (str): (optional) script to run on guest customization
            network: (str): (optional) Name of the vApp network to connect.
                If omitted, the VM won't be connected to any network
            storage_profile: (str): (optional) the name of the storage profile
                to be used for this VM

        :return: SourcedItem: (:class:`lxml.objectify.StringElement`): object
            representing the 'SourcedItem' xml object created from the
            specification.
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
        """Recompose the vApp and add VMs.

        :param specs: An array of VM specifications, see `to_sourced_item()`
            method for specification details.
        :param deploy: (bool): True if the vApp should be deployed at
            instantiation
        :param power_on: (bool): True if the vApp should be powered-on at
            instantiation
        :param all_eulas_accepted: (bool): True confirms acceptance of all
            EULAs in the vApp.

        :return:  A :class:`lxml.objectify.StringElement` object representing a
            sparsely populated vApp element.

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
