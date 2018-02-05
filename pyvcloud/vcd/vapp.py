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

from pyvcloud.vcd.acl import Acl
from pyvcloud.vcd.client import E
from pyvcloud.vcd.client import E_OVF
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import FenceMode
from pyvcloud.vcd.client import find_link
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.vdc import VDC


class VApp(object):
    def __init__(self, client, name=None, href=None, resource=None):
        self.client = client
        self.name = name
        if href is None and resource is None:
            raise TypeError("VApp initialization failed as arguments"
                            " are either invalid or None")
        self.href = href
        self.resource = resource
        if resource is not None:
            self.name = resource.get('name')
            self.href = resource.get('href')

    def get_resource(self):
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        return self.resource

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
        """Change the ownership of vApp to a given user.

        :param href: Href of the new owner or user.
        :return: None.
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        new_owner = self.resource.Owner
        new_owner.User.set('href', href)
        objectify.deannotate(new_owner)
        etree.cleanup_namespaces(new_owner)
        return self.client.put_resource(
            self.resource.get('href') + '/owner/', new_owner,
            EntityType.OWNER.value)

    def deploy(self, power_on=None, force_customization=None):
        """Deploys the vApp.

        Deploying the vApp will allocate all resources assigned to the vApp.
        TODO: Add lease_deployment_seconds param after PR 2036925 is fixed.
        https://jira.eng.vmware.com/browse/VCDA-465
        :param power_on: (bool): Specifies whether to power on/off vapp/VM

        on deployment. True by default, unless otherwise specified.
        :param lease_deployment_seconds: (str): Deployment lease in seconds.
        :param force_customization: (bool): Used to specify whether to force

        customization on deployment, if not set default value is false.

        :return: A :class:`lxml.objectify.StringElement` object describing
            the asynchronous Task deploying the vApp.
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        deploy_vapp_params = E.DeployVAppParams()
        if power_on is not None:
            deploy_vapp_params.set('powerOn', str(power_on).lower())
        if force_customization is not None:
            deploy_vapp_params.set('forceCustomization',
                                   str(force_customization).lower())
        return self.client.post_linked_resource(
            self.resource, RelationType.DEPLOY, EntityType.DEPLOY.value,
            deploy_vapp_params)

    def undeploy(self, action='default'):
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        params = E.UndeployVAppParams(E.UndeployPowerAction(action))
        return self.client.post_linked_resource(
            self.resource, RelationType.UNDEPLOY, EntityType.UNDEPLOY.value,
            params)

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
        """Shutdown the vApp.

        :return: A :class:`lxml.objectify.StringElement` object describing
            the asynchronous Task shutting down the vApp.
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        return self.client.post_linked_resource(
            self.resource, RelationType.POWER_SHUTDOWN, None, None)

    def power_reset(self):
        """Resets a vApp.

        :return: A :class:`lxml.objectify.StringElement` object describing
            the asynchronous Task resetting the vApp.
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        return self.client.post_linked_resource(
            self.resource, RelationType.POWER_RESET, None, None)

    def reboot(self):
        """Reboots the vApp.

        :return: A :class:`lxml.objectify.StringElement` object describing
            the asynchronous Task rebooting the vApp.
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        return self.client.post_linked_resource(
            self.resource, RelationType.POWER_REBOOT, None, None)

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
        """Attach the independent disk to the VM with the given name.

        :param disk_href: (str): The href of the disk to be attached.
        :param vm_name: (str): The name of the VM to which the disk
            will be attached.

        :return:  A :class:`lxml.objectify.StringElement` object describing
            the asynchronous Task of attaching the disk.

        :raises: Exception: If the named VM cannot be located or another error
            occurs.
        """
        disk_attach_or_detach_params = E.DiskAttachOrDetachParams(
            E.Disk(type=EntityType.DISK.value, href=disk_href))
        vm = self.get_vm(vm_name)

        return self.client.post_linked_resource(
            vm, RelationType.DISK_ATTACH,
            EntityType.DISK_ATTACH_DETACH_PARAMS.value,
            disk_attach_or_detach_params)

    def detach_disk_from_vm(self, disk_href, vm_name):
        """Detach the independent disk from the VM with the given name.

        :param disk_href: (str): The href of the disk to be detached.
        :param vm_name: (str): The name of the VM to which the disk
            will be detached.

        :return:  A :class:`lxml.objectify.StringElement` object describing
            the asynchronous Task of detaching the disk.

        :raises: Exception: If the named VM cannot be located or another error
            occurs.
        """
        disk_attach_or_detach_params = E.DiskAttachOrDetachParams(
            E.Disk(type=EntityType.DISK.value, href=disk_href))
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
        raise Exception('Can\'t find VM \'%s\'' % vm_name)

    def add_disk_to_vm(self, vm_name, disk_size):
        """Add a virtual disk to a virtual machine in the vApp.

        It assumes that the VM has already at least one virtual hard disk
            and will attempt to create another one with similar
            characteristics.

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

    def get_access_settings(self):
        """Get the access settings of the vapp.

        :return:  A :class:`lxml.objectify.StringElement` object representing
            the access settings of the vapp.
        """
        acl = Acl(self.client, self.get_resource())
        return acl.get_access_settings()

    def add_access_settings(self, access_settings_list=None):
        """Add access settings to a particular vapp.

        :param access_settings_list: (list of dict): list of access_setting
            in the dict format. Each dict contains:
            - type: (str): type of the subject. Only 'user' allowed for vapp.
            - name: (str): name of the user.
            - access_level: (str): access_level of the particular subject. One
                of 'ReadOnly', 'Change', 'FullControl'

        :return:  A :class:`lxml.objectify.StringElement` object representing
        the updated access control setting of the vapp.
        """
        acl = Acl(self.client, self.get_resource())
        return acl.add_access_settings(access_settings_list)

    def remove_access_settings(self,
                               access_settings_list=None,
                               remove_all=False):
        """Remove access settings from a particular vapp.

        :param access_settings_list: (list of dict): list of access_setting
            in the dict format. Each dict contains:
            - type: (str): type of the subject. Only 'user' allowed for vapp.
            - name: (str): name of the user.
        :param remove_all: (bool) : True if all access settings of the vapp
            should be removed

        :return:  A :class:`lxml.objectify.StringElement` object representing
            the updated access control setting of the vapp.
        """
        acl = Acl(self.client, self.get_resource())
        return acl.remove_access_settings(access_settings_list, remove_all)

    def share_with_org_members(self, everyone_access_level='ReadOnly'):
        """Share the vapp to all members of the organization.

        :param everyone_access_level: (str) : access level when sharing the
            vapp with everyone. One of 'ReadOnly', 'Change', 'FullControl'.
            'ReadOnly' by default.

        :return:  A :class:`lxml.objectify.StringElement` object representing
            the updated access control setting of the vapp.
        """
        acl = Acl(self.client, self.get_resource())
        return acl.share_with_org_members(everyone_access_level)

    def unshare_from_org_members(self):
        """Unshare the vapp from all members of current organization.

        :return:  A :class:`lxml.objectify.StringElement` object representing
            the updated access control setting of the vapp.
        """
        acl = Acl(self.client, self.get_resource())
        return acl.unshare_from_org_members()

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

    def delete_vms(self, names):
        """Recompose the vApp and delete VMs.

        :param names: A list or tuple of names (str) of the VMs to delete
            from the vApp.

        :return:  A :class:`lxml.objectify.StringElement` object representing a
            sparsely populated vApp element.
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
        """Connect the vapp to an orgvdc network.

        :param orgvdc_network_name: (str): name of the orgvdc network to be
            connected
        :param retain_ip: (bool): True if  the network resources such as
            IP/MAC of router will be retained across deployments.
        :param is_deployed: (bool): True if this orgvdc network has been
            deployed.
        :param fence_mode: (str): Controls connectivity to the parent
            network. One of bridged, isolated or natRouted. bridged by default.

        :return:  A :class:`lxml.objectify.StringElement` object representing
            the asynchronous task that is connecting the network.

        :raises: Exception: If orgvdc network does not exist in the vdc or if
        it is already connected to the vapp.
        """
        vdc = VDC(
            self.client,
            href=find_link(self.resource, RelationType.UP,
                           EntityType.VDC.value).href)
        orgvdc_networks = \
            vdc.list_orgvdc_network_resources(orgvdc_network_name)
        if len(orgvdc_networks) == 0:
            raise Exception("Orgvdc network \'%s\' does not exist in vdc "
                            "\'%s\'" % (orgvdc_network_name,
                                        vdc.get_resource().get('name')))
        orgvdc_network_href = orgvdc_networks[0].get('href')

        network_configuration_section = \
            deepcopy(self.resource.NetworkConfigSection)

        matched_orgvdc_network_config = \
            self._search_for_network_config_by_name(
                orgvdc_network_name, network_configuration_section)
        if matched_orgvdc_network_config is not None:
            raise Exception("Orgvdc network \'%s\' is already connected to "
                            "vapp." % orgvdc_network_name)

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
        """Disconnect the vapp from an orgvdc network.

        :param orgvdc_network_name: (str): name of the orgvdc
            network to be disconnected.

        :return:  A :class:`lxml.objectify.StringElement` object representing
            the asynchronous task that is disconnecting the network.

        :raises: Exception: If orgvdc network is not connected to the vapp.
        """
        network_configuration_section = \
            deepcopy(self.resource.NetworkConfigSection)

        matched_orgvdc_network_config = \
            self._search_for_network_config_by_name(
                orgvdc_network_name, network_configuration_section)
        if matched_orgvdc_network_config is None:
            raise Exception("Orgvdc network \'%s\' is not attached to the vapp"
                            % orgvdc_network_name)
        else:
            network_configuration_section.remove(matched_orgvdc_network_config)

        return self.client.put_linked_resource(
            self.resource.NetworkConfigSection, RelationType.EDIT,
            EntityType.NETWORK_CONFIG_SECTION.value,
            network_configuration_section)

    @staticmethod
    def _search_for_network_config_by_name(orgvdc_network_name,
                                           network_configuration_section):
        """Search for the NetworkConfig element by orgvdc network name.

        :param orgvdc_network_name: (str): name of the orgvdc network to be
            searched.
        :param network_configuration_section :(lxml.objectify.StringElement):
            NetworkConfigSection of a vapp.

        :return: A :class:`lxml.objectify.StringElement` object
            representing the  NetworkConfig element in NetworkConfigSection.
        """
        if hasattr(network_configuration_section, 'NetworkConfig'):
            for network_config in network_configuration_section.NetworkConfig:
                if network_config.get('networkName') == orgvdc_network_name:
                    return network_config
        return None
