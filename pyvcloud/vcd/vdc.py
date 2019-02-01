# VMware vCloud Director Python SDK
# Copyright (c) 2014-2018 VMware, Inc. All Rights Reserved.
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

from lxml import etree

from pyvcloud.vcd.acl import Acl
from pyvcloud.vcd.client import E
from pyvcloud.vcd.client import E_OVF
from pyvcloud.vcd.client import EdgeGatewayType
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import FenceMode
from pyvcloud.vcd.client import find_link
from pyvcloud.vcd.client import GatewayBackingConfigType
from pyvcloud.vcd.client import MetadataDomain
from pyvcloud.vcd.client import MetadataValueType
from pyvcloud.vcd.client import MetadataVisibility
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import QueryResultFormat
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.client import ResourceType
from pyvcloud.vcd.exceptions import EntityNotFoundException
from pyvcloud.vcd.exceptions import InvalidParameterException
from pyvcloud.vcd.exceptions import MultipleRecordsException
from pyvcloud.vcd.metadata import Metadata
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.platform import Platform
from pyvcloud.vcd.utils import cidr_to_netmask
from pyvcloud.vcd.utils import get_admin_href
from pyvcloud.vcd.utils import netmask_to_cidr_prefix_len


class VDC(object):
    def __init__(self, client, name=None, href=None, resource=None):
        """Constructor for VDC objects.

        :param pyvcloud.vcd.client.Client client: the client that will be used
            to make REST calls to vCD.
        :param str name: name of the entity.
        :param str href: URI of the entity.
        :param lxml.objectify.ObjectifiedElement resource: object containing
            EntityType.VDC XML data representing the org vdc.
        """
        self.client = client
        self.name = name
        if href is None and resource is None:
            raise InvalidParameterException(
                "VDC initialization failed as arguments are either invalid "
                "or None")
        self.href = href
        self.resource = resource
        if resource is not None:
            self.name = resource.get('name')
            self.href = resource.get('href')
        self.href_admin = get_admin_href(self.href)

    def get_resource(self):
        """Fetches the XML representation of the org vdc from vCD.

        Will serve cached response if possible.

        :return: object containing EntityType.VDC XML data representing the
            org vdc.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.reload()
        return self.resource

    def get_resource_href(self, name, entity_type=EntityType.VAPP):
        """Fetches href of a vApp in the org vdc from vCD.

        :param str name: name of the vApp.
        :param pyvcloud.vcd.client.EntityType entity_type: type of entity we
            want to retrieve. *Please note that this function is incapable of
            returning anything other than vApps at this point.*

        :return: href of the vApp identified by its name.

        :rtype: str

        :raises: EntityNotFoundException: if the named vApp can not be found.
        :raises: MultipleRecordsException: if more than one vApp with the
            provided name are found.
        """
        self.get_resource()
        result = []
        if hasattr(self.resource, 'ResourceEntities') and \
           hasattr(self.resource.ResourceEntities, 'ResourceEntity'):
            for vapp in self.resource.ResourceEntities.ResourceEntity:
                if entity_type is None or \
                   entity_type.value == vapp.get('type'):
                    if vapp.get('name') == name:
                        result.append(vapp.get('href'))
        if len(result) == 0:
            raise EntityNotFoundException('vApp named \'%s\' not found' % name)

        elif len(result) > 1:
            raise MultipleRecordsException("Found multiple vApps named '%s', \
                use the vapp-id to identify." % name)
        return result[0]

    def reload(self):
        """Reloads the resource representation of the org vdc.

        This method should be called in between two method invocations on the
        VDC object, if the former call changes the representation of the
        org vdc in vCD.
        """
        self.resource = self.client.get_resource(self.href)
        if self.resource is not None:
            self.name = self.resource.get('name')
            self.href = self.resource.get('href')

    def get_vapp(self, name):
        """Fetches XML representation of a vApp in the org vdc from vCD.

        :param str name: name of the vApp.

        :return: object containing EntityType.VAPP XML data representing the
            vApp.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: EntityNotFoundException: if the named vApp can not be found.
        :raises: MultipleRecordsException: if more than one vApp with the
            provided name are found.
        """
        return self.client.get_resource(self.get_resource_href(name))

    def delete_vapp(self, name, force=False):
        """Delete a vApp in the current org vdc.

        :param str name: name of the vApp to be deleted.

        :raises: EntityNotFoundException: if the named vApp can not be found.
        :raises: MultipleRecordsException: if more than one vApp with the
            provided name are found.
        """
        href = self.get_resource_href(name)
        return self.client.delete_resource(href, force)

    # NOQA refer to http://pubs.vmware.com/vcd-820/index.jsp?topic=%2Fcom.vmware.vcloud.api.sp.doc_27_0%2FGUID-BF9B790D-512E-4EA1-99E8-6826D4B8E6DC.html
    def instantiate_vapp(self,
                         name,
                         catalog,
                         template,
                         description=None,
                         network=None,
                         fence_mode=FenceMode.BRIDGED.value,
                         ip_allocation_mode='dhcp',
                         deploy=True,
                         power_on=True,
                         accept_all_eulas=False,
                         memory=None,
                         cpu=None,
                         disk_size=None,
                         password=None,
                         cust_script=None,
                         vm_name=None,
                         hostname=None,
                         ip_address=None,
                         storage_profile=None,
                         network_adapter_type=None):
        """Instantiate a vApp from a vApp template in a catalog.

        If customization parameters are provided, it will customize the vm and
        guest OS, taking some assumptions.

        A general assumption is made by this method that there is only one vm
        in the vApp. And the vm has only one NIC.

        :param str name: name of the new vApp.
        :param str catalog: name of the catalog.
        :param str template: name of the vApp template.
        :param str description: description of the new vApp.
        :param str network: name of a vdc network. When provided, connects the
            vm to the network.
        :param str fence_mode: fence mode. Possible values are
            pyvcloud.vcd.client.FenceMode.BRIDGED.value and
            pyvcloud.vcd.client.FenceMode.NAT_ROUTED.value.
        :param str ip_allocation_mode: ip allocation mode. Acceptable values
            are `pool`, `dhcp` and `manual`.
        :param bool deploy: if True deploy the vApp after instantiation.
        :param bool power_on: if True, power on the vApp after instantiation.
        :param bool accept_all_eulas: True, confirms acceptance of all EULAs in
            a vApp template.
        :param int memory: size of memory of the first vm.
        :param int cpu: number of cpus in the first vm.
        :param int disk_size: size of the first disk of the first vm.
        :param str password: admin password of the guest os on the first vm.
        :param str cust_script: guest customization to run on the vm.
        :param str vm_name: when provided, sets the name of the vm.
        :param str ip_address: when provided, sets the ip_address of the vm.
        :param str hostname: when provided, sets the hostname of the guest OS.
        :param str storage_profile:
        :param str network_adapter_type: One of the values in
            pyvcloud.vcd.client.NetworkAdapterType.

        :return: an object containing EntityType.VAPP XML data which
            represents the new vApp.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        self.get_resource()

        # Get hold of the template
        org_href = find_link(self.resource, RelationType.UP,
                             EntityType.ORG.value).href
        org = Org(self.client, href=org_href)
        catalog_item = org.get_catalog_item(catalog, template)
        template_resource = self.client.get_resource(
            catalog_item.Entity.get('href'))

        # If network is not specified by user then default to
        # vApp network name specified in the template
        template_networks = template_resource.xpath(
            '//ovf:NetworkSection/ovf:Network',
            namespaces={'ovf': NSMAP['ovf']})
        assert len(template_networks) > 0
        network_name_from_template = template_networks[0].get(
            '{' + NSMAP['ovf'] + '}name')
        if ((network is None) and (network_name_from_template != 'none')):
            network = network_name_from_template

        # Find the network in vdc referred to by user, using
        # name of the network
        network_href = network_name = None
        if network is not None:
            if hasattr(self.resource, 'AvailableNetworks') and \
               hasattr(self.resource.AvailableNetworks, 'Network'):
                for n in self.resource.AvailableNetworks.Network:
                    if network == n.get('name'):
                        network_href = n.get('href')
                        network_name = n.get('name')
                        break
            if network_href is None:
                raise EntityNotFoundException(
                    'Network \'%s\' not found in the Virtual Datacenter.' %
                    network)

        # Configure the network of the vApp
        vapp_instantiation_param = None
        if network_name is not None:
            network_configuration = E.Configuration(
                E.ParentNetwork(href=network_href), E.FenceMode(fence_mode))

            if fence_mode == 'natRouted':
                # TODO(need to find the vm_id)
                vm_id = None
                network_configuration.append(
                    E.Features(
                        E.NatService(
                            E.IsEnabled('true'), E.NatType('ipTranslation'),
                            E.Policy('allowTraffic'),
                            E.NatRule(
                                E.OneToOneVmRule(
                                    E.MappingMode('automatic'),
                                    E.VAppScopedVmId(vm_id), E.VmNicId(0))))))

            vapp_instantiation_param = E.InstantiationParams(
                E.NetworkConfigSection(
                    E_OVF.Info('Configuration for logical networks'),
                    E.NetworkConfig(
                        network_configuration, networkName=network_name)))

        # Get all vms in the vapp template
        vms = template_resource.xpath(
            '//vcloud:VAppTemplate/vcloud:Children/vcloud:Vm',
            namespaces=NSMAP)
        assert len(vms) > 0

        vm_instantiation_param = E.InstantiationParams()

        if ip_allocation_mode == 'static':
            ip_allocation_mode = 'manual'

        # Configure network of the first vm
        if network_name is not None:
            primary_index = int(vms[0].NetworkConnectionSection.
                                PrimaryNetworkConnectionIndex.text)
            network_connection_param = E.NetworkConnection(
                E.NetworkConnectionIndex(primary_index), network=network_name)
            if ip_address is not None:
                network_connection_param.append(E.IpAddress(ip_address))
            network_connection_param.append(E.IsConnected('true'))
            network_connection_param.append(
                E.IpAddressAllocationMode(ip_allocation_mode.upper()))
            if network_adapter_type is not None:
                network_connection_param.append(
                    E.NetworkAdapterType(network_adapter_type))
            vm_instantiation_param.append(
                E.NetworkConnectionSection(
                    E_OVF.Info(
                        'Specifies the available VM network connections'),
                    network_connection_param))

        # Configure cpu, memory, disk of the first vm
        cpu_params = memory_params = disk_params = None
        if memory is not None or cpu is not None or disk_size is not None:
            virtual_hardware_section = E_OVF.VirtualHardwareSection(
                E_OVF.Info('Virtual hardware requirements'))
            items = vms[0].xpath(
                '//ovf:VirtualHardwareSection/ovf:Item',
                namespaces={'ovf': NSMAP['ovf']})
            for item in items:
                if memory is not None and memory_params is None:
                    if item['{' + NSMAP['rasd'] + '}ResourceType'] == 4:
                        item['{' + NSMAP['rasd'] + '}ElementName'] = \
                            '%s MB of memory' % memory
                        item['{' + NSMAP['rasd'] + '}VirtualQuantity'] = memory
                        memory_params = item
                        virtual_hardware_section.append(memory_params)

                if cpu is not None and cpu_params is None:
                    if item['{' + NSMAP['rasd'] + '}ResourceType'] == 3:
                        item['{' + NSMAP['rasd'] + '}ElementName'] = \
                            '%s virtual CPU(s)' % cpu
                        item['{' + NSMAP['rasd'] + '}VirtualQuantity'] = cpu
                        cpu_params = item
                        virtual_hardware_section.append(cpu_params)

                if disk_size is not None and disk_params is None:
                    if item['{' + NSMAP['rasd'] + '}ResourceType'] == 17:
                        item['{' + NSMAP['rasd'] + '}Parent'] = None
                        item['{' + NSMAP['rasd'] + '}HostResource'].attrib[
                            '{' + NSMAP['vcloud'] + '}capacity'] = \
                            '%s' % disk_size
                        item['{' + NSMAP['rasd'] + '}VirtualQuantity'] = \
                            disk_size * 1024 * 1024
                        disk_params = item
                        virtual_hardware_section.append(disk_params)
            vm_instantiation_param.append(virtual_hardware_section)

        # Configure guest customization for the vm
        if password is not None or cust_script is not None or \
           hostname is not None:
            guest_customization_param = E.GuestCustomizationSection(
                E_OVF.Info('Specifies Guest OS Customization Settings'),
                E.Enabled('true'),
            )
            if password is None:
                guest_customization_param.append(
                    E.AdminPasswordEnabled('false'))
            else:
                guest_customization_param.append(
                    E.AdminPasswordEnabled('true'))
                guest_customization_param.append(E.AdminPasswordAuto('false'))
                guest_customization_param.append(E.AdminPassword(password))
                guest_customization_param.append(
                    E.ResetPasswordRequired('false'))
            if cust_script is not None:
                guest_customization_param.append(
                    E.CustomizationScript(cust_script))
            if hostname is not None:
                guest_customization_param.append(E.ComputerName(hostname))
            vm_instantiation_param.append(guest_customization_param)

        # Craft the <SourcedItem> element for the first vm
        sourced_item = E.SourcedItem(
            E.Source(
                href=vms[0].get('href'),
                id=vms[0].get('id'),
                name=vms[0].get('name'),
                type=vms[0].get('type')))

        vm_general_params = E.VmGeneralParams()
        if vm_name is not None:
            vm_general_params.append(E.Name(vm_name))

        # TODO(check if it needs customization if network, cpu or memory...)
        if disk_size is None and \
           password is None and \
           cust_script is None and \
           hostname is None:
            needs_customization = 'false'
        else:
            needs_customization = 'true'
        vm_general_params.append(E.NeedsCustomization(needs_customization))
        sourced_item.append(vm_general_params)
        sourced_item.append(vm_instantiation_param)

        if storage_profile is not None:
            sp = self.get_storage_profile(storage_profile)
            vapp_storage_profile = E.StorageProfile(
                href=sp.get('href'),
                id=sp.get('href').split('/')[-1],
                type=sp.get('type'),
                name=sp.get('name'))
            sourced_item.append(vapp_storage_profile)

        # Cook the entire vApp Template instantiation element
        deploy_param = 'true' if deploy else 'false'
        power_on_param = 'true' if power_on else 'false'
        all_eulas_accepted = 'true' if accept_all_eulas else 'false'

        vapp_template_params = E.InstantiateVAppTemplateParams(
            name=name, deploy=deploy_param, powerOn=power_on_param)

        if description is not None:
            vapp_template_params.append(E.Description(description))

        if vapp_instantiation_param is not None:
            vapp_template_params.append(vapp_instantiation_param)

        vapp_template_params.append(
            E.Source(href=catalog_item.Entity.get('href')))

        vapp_template_params.append(sourced_item)

        vapp_template_params.append(E.AllEULAsAccepted(all_eulas_accepted))

        return self.client.post_linked_resource(
            self.resource, RelationType.ADD,
            EntityType.INSTANTIATE_VAPP_TEMPLATE_PARAMS.value,
            vapp_template_params)

    def list_resources(self, entity_type=None):
        """Fetch information about all resources in the current org vdc.

        :param str entity_type: filter to restrict type of resource we want to
            fetch. EntityType.VAPP.value and EntityType.VAPP_TEMPLATE.value
            both are acceptable values.

        :return: a list of dictionaries, where each dictionary represents a
            resource e.g. vApp templates, vApps. And each dictionary has 'name'
            and 'type' of the resource.

        :rtype: dict
        """
        self.get_resource()
        result = []
        if hasattr(self.resource, 'ResourceEntities') and \
           hasattr(self.resource.ResourceEntities, 'ResourceEntity'):
            for resource in self.resource.ResourceEntities.ResourceEntity:
                if entity_type is None or \
                   entity_type.value == resource.get('type'):
                    result.append({
                        'name': resource.get('name'),
                        'type': resource.get('type')
                    })
        return result

    def list_edge_gateways(self):
        """Fetch a list of edge gateways defined in a vdc.

        :return: a list of dictionaries, where each dictionary contains the
            name and href of an edge gateway.

        :rtype: list
        """
        self.get_resource()
        links = self.client.get_linked_resource(self.resource,
                                                RelationType.EDGE_GATEWAYS,
                                                EntityType.RECORDS.value)
        edge_gateways = []
        if hasattr(links, 'EdgeGatewayRecord'):
            for e in links.EdgeGatewayRecord:
                edge_gateways.append({
                    'name': e.get('name'),
                    'href': e.get('href')
                })
        return edge_gateways

    def create_disk(self,
                    name,
                    size,
                    bus_type=None,
                    bus_sub_type=None,
                    description=None,
                    storage_profile_name=None,
                    iops=None):
        """Request the creation of an independent disk.

        :param str name: name of the new disk.
        :param int size: size of the new disk in bytes.
        :param str bus_type: bus type of the new disk.
        :param str bus_sub_type: bus subtype of the new disk.
        :param str description: description of the new disk.
        :param str storage_profile_name: name of an existing storage profile to
            be used by the new disk.
        :param int iops: iops requirement of the new disk.

        :return: an object containing EntityType.DISK XML data which represents
            the new disk being created along with the the asynchronous task
            that is creating the disk.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        self.get_resource()

        disk_params = E.DiskCreateParams(E.Disk(name=name, size=str(size)))
        if iops is not None:
            disk_params.Disk.set('iops', iops)

        if description is not None:
            disk_params.Disk.append(E.Description(description))

        if bus_type is not None and bus_sub_type is not None:
            disk_params.Disk.set('busType', bus_type)
            disk_params.Disk.set('busSubType', bus_sub_type)

        if storage_profile_name is not None:
            storage_profile = self.get_storage_profile(storage_profile_name)
            disk_params.Disk.append(
                E.StorageProfile(
                    name=storage_profile_name,
                    href=storage_profile.get('href'),
                    type=storage_profile.get('type')))

        return self.client.post_linked_resource(
            self.resource, RelationType.ADD,
            EntityType.DISK_CREATE_PARMS.value, disk_params)

    def update_disk(self,
                    name=None,
                    disk_id=None,
                    new_name=None,
                    new_size=None,
                    new_description=None,
                    new_storage_profile_name=None,
                    new_iops=None):
        """Update an existing independent disk.

        :param str name: name of the existing disk.
        :param str disk_id: id of the existing disk.
        :param str new_name: new name of the disk.
        :param str new_size: new size of the disk in bytes.
        :param str new_description: new description of the disk.
        :param str new_storage_profile_name: new storage profile that the disk
            will be moved to.
        :param int new_iops: new iops requirement of the disk.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is updating the disk.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: EntityNotFoundException: if the named disk cannot be located.
        """
        self.get_resource()

        if disk_id is not None:
            disk = self.get_disk(disk_id=disk_id)
        else:
            disk = self.get_disk(name=name)

        disk_params = E.Disk()
        if new_name is not None:
            disk_params.set('name', new_name)
        else:
            disk_params.set('name', disk.get('name'))

        if new_size is not None:
            disk_params.set('size', str(new_size))
        else:
            disk_params.set('size', disk.get('size'))

        if new_description is not None:
            disk_params.append(E.Description(new_description))

        if new_storage_profile_name is not None:
            new_sp = self.get_storage_profile(new_storage_profile_name)
            disk_params.append(
                E.StorageProfile(
                    name=new_storage_profile_name,
                    href=new_sp.get('href'),
                    type=new_sp.get('type')))

        if new_iops is not None:
            disk_params.set('iops', str(new_iops))

        return self.client.put_linked_resource(
            disk, RelationType.EDIT, EntityType.DISK.value, disk_params)

    def delete_disk(self, name=None, disk_id=None):
        """Delete an existing independent disk.

        :param str name: name of the disk to delete.
        :param str disk_id: id of the disk to delete.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is deleting the disk.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: EntityNotFoundException: if the named disk cannot be located.
        """
        self.get_resource()

        if disk_id is not None:
            disk = self.get_disk(disk_id=disk_id)
        else:
            disk = self.get_disk(name=name)

        return self.client.delete_linked_resource(disk, RelationType.REMOVE,
                                                  None)

    def get_disks(self):
        """Request a list of independent disks defined in the vdc.

        :return: a list of objects, where each object is an
            lxml.objectify.ObjectifiedElement containing EntityType.DISK XML
            element representing an independent disk. The object also contain
            information of all the vms to which the independent disk is
            attached to.

        :rtype: list
        """
        self.get_resource()

        disks = []
        if hasattr(self.resource, 'ResourceEntities') and \
           hasattr(self.resource.ResourceEntities, 'ResourceEntity'):
            for resourceEntity in \
                    self.resource.ResourceEntities.ResourceEntity:

                if resourceEntity.get('type') == EntityType.DISK.value:
                    disk = self.client.get_resource(resourceEntity.get('href'))
                    attached_vms = self.client.get_linked_resource(
                        disk, RelationType.DOWN, EntityType.VMS.value)
                    disk['attached_vms'] = attached_vms
                    disks.append(disk)
        return disks

    def get_disk(self, name=None, disk_id=None):
        """Return information for an independent disk.

        :param str name: name of the disk.
        :param str disk_id: id of the disk.

        :return: an object containing EntityType.DISK XML data which represents
            the disk.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: InvalidParameterException: if neither name nor the disk_id
            param is specified.
        :raises: EntityNotFoundException: if the named disk cannot be located.
        """
        if name is None and disk_id is None:
            raise InvalidParameterException(
                'Unable to idendify disk without name or id.')

        self.get_resource()

        disks = self.get_disks()

        result = None
        if disk_id is not None:
            if not disk_id.startswith('urn:vcloud:disk:'):
                disk_id = 'urn:vcloud:disk:' + disk_id
            for disk in disks:
                if disk.get('id') == disk_id:
                    result = disk
                    # disk-id's are unique so it is ok to break the loop
                    # and stop looking further.
                    break
        elif name is not None:
            for disk in disks:
                if disk.get('name') == name:
                    if result is None:
                        result = disk
                    else:
                        raise MultipleRecordsException(
                            'Found multiple disks with name %s'
                            ', please identify disk via disk-id.' %
                            disk.get('name'))
        if result is None:
            raise EntityNotFoundException(
                'No disk found with the given name/id.')
        else:
            return result

    def change_disk_owner(self, user_href, name=None, disk_id=None):
        """Change the ownership of an independent disk to a given user.

        :param str user_href: href of the new owner.
        :param str name: name of the independent disk.
        :param str disk_id: id of the disk (required if there are multiple
            disks with same name).

        :raises: EntityNotFoundException: if the named disk cannot be located.
        """
        self.get_resource()

        if disk_id is not None:
            disk = self.get_disk(disk_id=disk_id)
        else:
            disk = self.get_disk(name=name)

        new_owner = disk.Owner
        new_owner.User.set('href', user_href)
        etree.cleanup_namespaces(new_owner)
        return self.client.put_resource(
            disk.get('href') + '/owner/', new_owner, EntityType.OWNER.value)

    def get_storage_profiles(self):
        """Fetch a list of the Storage Profiles defined in a vdc.

        :return: a list of lxml.objectify.ObjectifiedElement objects, where
            each object contains VdcStorageProfile XML element representing an
            existing storage profile.

        :rtype: list
        """
        profile_list = []
        self.get_resource()

        if hasattr(self.resource, 'VdcStorageProfiles') and \
           hasattr(self.resource.VdcStorageProfiles, 'VdcStorageProfile'):
            for profile in self.resource.VdcStorageProfiles.VdcStorageProfile:
                profile_list.append(profile)
            return profile_list
        return None

    def get_all_metadata(self):
        """Fetch all metadata entries of the org vdc.

        :return: an object containing EntityType.METADATA XML data which
            represents the metadata entries associated with the org vdc.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        self.get_resource()
        return self.client.get_linked_resource(
            self.resource, RelationType.DOWN, EntityType.METADATA.value)

    def get_metadata_value(self, key, domain=MetadataDomain.GENERAL):
        """Fetch a metadata value identified by the domain and key.

        :param str key: key of the value to be fetched.
        :param client.MetadataDomain domain: domain of the value to be fetched.

        :return: an object containing EntityType.METADATA_VALUE XML data which
            represents the metadata value.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        metadata = Metadata(client=self.client,
                            resource=self.get_all_metadata())
        return metadata.get_metadata_value(key, domain)

    def set_metadata(self,
                     key,
                     value,
                     domain=MetadataDomain.GENERAL,
                     visibility=MetadataVisibility.READ_WRITE,
                     metadata_value_type=MetadataValueType.STRING):
        """Add a metadata entry to the org vdc.

        Only admins can perform this operation. If an entry with the same key
        exists, it will be updated with the new value.

        :param str key: an arbitrary key name. Length cannot exceed 256 UTF-8
            characters.
        :param str value: value of the metadata entry
        :param client.MetadataDomain domain: domain where the new entry would
            be put.
        :param client.MetadataVisibility visibility: visibility of the metadata
            entry.
        :param client.MetadataValueType metadata_value_type:

        :return: an object of type EntityType.TASK XML which represents
            the asynchronous task that is updating the metadata on the org vdc.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        metadata = Metadata(client=self.client,
                            resource=self.get_all_metadata())
        return metadata.set_metadata(key=key,
                                     value=value,
                                     domain=domain,
                                     visibility=visibility,
                                     metadata_value_type=metadata_value_type,
                                     use_admin_endpoint=True)

    def set_multiple_metadata(self,
                              key_value_dict,
                              domain=MetadataDomain.GENERAL,
                              visibility=MetadataVisibility.READ_WRITE,
                              metadata_value_type=MetadataValueType.STRING):
        """Add multiple metadata entries to the org vdc.

        Only Sys admins can perform this operation. If an entry with the same
        key exists, it will be updated with the new value.

        :param dict key_value_dict: a dict containing key-value pairs to be
            added/updated.
        :param client.MetadataDomain domain: domain where the new entries would
            be put.
        :param client.MetadataVisibility visibility: visibility of the metadata
            entries.
        :param client.MetadataValueType metadata_value_type:

        :return: an object of type EntityType.TASK XML which represents
            the asynchronous task that is updating the metadata on the org vdc.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        metadata = Metadata(client=self.client,
                            resource=self.get_all_metadata())
        return metadata.set_multiple_metadata(
            key_value_dict=key_value_dict,
            domain=domain,
            visibility=visibility,
            metadata_value_type=metadata_value_type,
            use_admin_endpoint=True)

    def remove_metadata(self, key, domain=MetadataDomain.GENERAL):
        """Remove a metadata entry from the org vdc.

        Only admins can perform this operation.

        :param str key: key of the metadata to be removed.
        :param client.MetadataDomain domain: domain of the entry to be removed.

        :return: an object of type EntityType.TASK XML which represents
            the asynchronous task that is deleting the metadata on the org vdc.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: AccessForbiddenException: If there is no metadata entry
            corresponding to the key provided.
        """
        metadata = Metadata(client=self.client,
                            resource=self.get_all_metadata())
        return metadata.remove_metadata(key=key,
                                        domain=domain,
                                        use_admin_endpoint=True)

    def get_storage_profile(self, profile_name):
        """Fetch a specific Storage Profile within an org vdc.

        :param str profile_name: name of the requested storage profile.

        :return: an object containing VdcStorageProfile XML element that
            represents the requested storage profile.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        self.get_resource()

        if hasattr(self.resource, 'VdcStorageProfiles') and \
           hasattr(self.resource.VdcStorageProfiles, 'VdcStorageProfile'):
            for profile in self.resource.VdcStorageProfiles.VdcStorageProfile:
                if profile.get('name') == profile_name:
                    return profile

        raise EntityNotFoundException(
            'Storage Profile named \'%s\' not found' % profile_name)

    def enable_vdc(self, enable=True):
        """Enable current vdc.

        :param bool enable: True, to enable the vdc. False, to disable the vdc.

        :return: an object containing EntityType.VDC XML data representing the
            updated org vdc.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        resource_admin = self.client.get_resource(self.href_admin)
        if enable:
            rel = RelationType.ENABLE
        else:
            rel = RelationType.DISABLE

        return self.client.post_linked_resource(resource_admin, rel, None,
                                                None)

    def delete_vdc(self):
        """Delete the current org vdc.

        :param str vdc_name: name of the org vdc to delete.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is deleting the org vdc.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        self.get_resource()

        return self.client.delete_linked_resource(self.resource,
                                                  RelationType.REMOVE, None)

    def get_access_settings(self):
        """Get the access settings of the vdc.

        :return: an object containing EntityType.CONTROL_ACCESS_PARAMS which
            represents the access control list of the vdc.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        acl = Acl(self.client, self.get_resource())
        return acl.get_access_settings()

    def add_access_settings(self, access_settings_list=None):
        """Add access settings to the vdc.

        :param list access_settings_list: list of dictionaries, where each
            dictionary represents a single access setting. The dictionary
            structure is as follows,

            - type: (str): type of the subject. One of 'org' or 'user'.
            - name: (str): name of the user or org.
            - access_level: (str): access_level of the particular subject.
                Allowed values are 'ReadOnly', 'Change' or 'FullControl'.

        :return: an object containing EntityType.CONTROL_ACCESS_PARAMS XML
            data representing the updated Access Control List of the vdc.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        acl = Acl(self.client, self.get_resource())
        return acl.add_access_settings(access_settings_list)

    def remove_access_settings(self,
                               access_settings_list=None,
                               remove_all=False):
        """Remove access settings from the vdc.

        :param list access_settings_list: list of dictionaries, where each
            dictionary represents a single access setting. The dictionary
            structure is as follows,

            - type: (str): type of the subject. One of 'org' or 'user'.
            - name: (str): name of the user or org.
        :param bool remove_all: True, if the entire Access Control List of the
            vdc should be removed, else False.

        :return: an object containing EntityType.CONTROL_ACCESS_PARAMS XML
            data representing the updated access control setting of the vdc.

        :rtype: lxml.objectify.ObjectifiedElement`
        """
        acl = Acl(self.client, self.get_resource())
        return acl.remove_access_settings(access_settings_list, remove_all)

    def share_with_org_members(self, everyone_access_level='ReadOnly'):
        """Share the vdc to all members of the organization.

        :param str everyone_access_level: level of access granted while
            sharing the vdc with everyone. 'ReadOnly' is the only allowed
            value.

        :return: an object containing EntityType.CONTROL_ACCESS_PARAMS XML
            data representing the updated access control setting of the vdc.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        acl = Acl(self.client, self.get_resource())
        return acl.share_with_org_members(everyone_access_level)

    def unshare_from_org_members(self):
        """Unshare the vdc from all members of current organization.

        Should give individual access to at least one user before unsharing
        access to the whole org.

        :return: an object containing EntityType.CONTROL_ACCESS_PARAMS XML
            data representing the updated access control setting of the vdc.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        acl = Acl(self.client, self.get_resource())
        return acl.unshare_from_org_members()

    def create_vapp(self,
                    name,
                    description=None,
                    network=None,
                    fence_mode=FenceMode.BRIDGED.value,
                    accept_all_eulas=None):
        """Create a new vApp in this vdc.

        :param str name: name of the new vApp.
        :param str description: description of the new vApp.
        :param str network: name of the org vdc network that the vApp will
            connect to.
        :param str fence_mode: network fence mode. Acceptable values are
            pyvcloud.vcd.client.FenceMode.BRIDGED.value and
            pyvcloud.vcd.client.FenceMode.NAT_ROUTED.value.
        :param bool accept_all_eulas: True confirms acceptance of all EULAs
            for the vApp template.

        :return: an object containing EntityType.VAPP XML data which represents
            the new created vApp in the org vdc.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        self.get_resource()

        network_href = network_name = None
        if network is not None:
            if hasattr(self.resource, 'AvailableNetworks') and \
               hasattr(self.resource.AvailableNetworks, 'Network'):
                for n in self.resource.AvailableNetworks.Network:
                    if network == n.get('name'):
                        network_href = n.get('href')
                        network_name = n.get('name')
                        break
            if network_href is None:
                raise EntityNotFoundException(
                    'Network \'%s\' not found in the Virtual Datacenter.' %
                    network)

        vapp_instantiation_param = None
        if network_name is not None:
            network_configuration = E.Configuration(
                E.ParentNetwork(href=network_href), E.FenceMode(fence_mode))

            vapp_instantiation_param = E.InstantiationParams(
                E.NetworkConfigSection(
                    E_OVF.Info('Configuration for logical networks'),
                    E.NetworkConfig(
                        network_configuration, networkName=network_name)))

        params = E.ComposeVAppParams(name=name)
        if description is not None:
            params.append(E.Description(description))
        if vapp_instantiation_param is not None:
            params.append(vapp_instantiation_param)
        if accept_all_eulas is not None:
            params.append(E.AllEULAsAccepted(accept_all_eulas))

        return self.client.post_linked_resource(
            self.resource, RelationType.ADD,
            EntityType.COMPOSE_VAPP_PARAMS.value, params)

    def create_routed_vdc_network(self,
                                  network_name,
                                  gateway_name,
                                  network_cidr,
                                  description=None,
                                  primary_dns_ip=None,
                                  secondary_dns_ip=None,
                                  dns_suffix=None,
                                  ip_range_start=None,
                                  ip_range_end=None,
                                  is_shared=None,
                                  guest_vlan_allowed=None,
                                  sub_interface=None,
                                  distributed_interface=None,
                                  retain_net_info_across_deployments=False):
        """Create a new Routed org vdc network in this vdc.

        :param str network_name: name of the new network.
        :param str gateway_name: name of an existing edge Gateway
                                 appliance that will manage the virtual
                                 network.
        :param str network_cidr: CIDR in the format of 10.2.2.1/20.
        :param str description: description of the new network.
        :param str primary_dns_ip: IP address of primary DNS server.
        :param str secondary_dns_ip: IP address of secondary DNS Server.
        :param str dns_suffix: DNS suffix.
        :param str ip_range_start: start address of the IP ranges used for
                                   static pool allocation in the network.
        :param str ip_range_end: end address of the IP ranges used for static
                                 pool allocation in the network.
        :param bool is_shared: True, if the network is shared with other vdc(s)
                               in the organization, else False.
        :param bool guest_vlan_allowed: True if Network allows guest VLAN
                                        tagging
        :param bool sub_interface: True if Network is connected to an Edge
                                   Gateway subinterface.
        :param bool distributed_interface: True if Network is connected to a
                                           distributed logical router.
        :param bool retain_net_info_across_deployments: Specifies whether the
                                                        network resources such
                                                        as IP/MAC of router
                                                        will be retained across
                                                        deployments. Default is
                                                        false.

        :return: an object containing EntityType.ORG_VDC_NETWORK XML data which
                 represents an org vdc network.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        gateway_ip, netmask = cidr_to_netmask(network_cidr)

        self.get_resource()

        request_payload = E.OrgVdcNetwork(name=network_name)
        if description is not None:
            request_payload.append(E.Description(description))

        vdc_network_configuration = E.Configuration()
        ip_scope = E.IpScope()
        ip_scope.append(E.IsInherited('false'))
        ip_scope.append(E.Gateway(gateway_ip))
        ip_scope.append(E.Netmask(netmask))
        if primary_dns_ip is not None:
            ip_scope.append(E.Dns1(primary_dns_ip))
        if secondary_dns_ip is not None:
            ip_scope.append(E.Dns2(secondary_dns_ip))
        if dns_suffix is not None:
            ip_scope.append(E.DnsSuffix(dns_suffix))
        if ip_range_start is not None and ip_range_end is not None:
            ip_range = E.IpRange()
            ip_range.append(E.StartAddress(ip_range_start))
            ip_range.append(E.EndAddress(ip_range_end))
            ip_scope.append(E.IpRanges(ip_range))
        vdc_network_configuration.append(E.IpScopes(ip_scope))
        vdc_network_configuration.append(
            E.FenceMode(FenceMode.NAT_ROUTED.value))
        if retain_net_info_across_deployments is not None:
            vdc_network_configuration.append(
                E.RetainNetInfoAcrossDeployments(
                    retain_net_info_across_deployments))
        if sub_interface is not None:
            vdc_network_configuration.append(
                E.SubInterface(sub_interface))
        if distributed_interface is not None:
            vdc_network_configuration.append(
                E.DistributedInterface(distributed_interface))
        if guest_vlan_allowed is not None:
            vdc_network_configuration.append(
                E.GuestVlanAllowed(guest_vlan_allowed))
        request_payload.append(vdc_network_configuration)

        gateway = self.get_gateway(gateway_name)
        gateway_href = gateway.get('href')
        request_payload.append(E.EdgeGateway(href=gateway_href))

        if is_shared is not None:
            request_payload.append(E.IsShared(is_shared))

        return self.client.post_linked_resource(
            self.resource, RelationType.ADD, EntityType.ORG_VDC_NETWORK.value,
            request_payload)

    def create_directly_connected_vdc_network(self,
                                              network_name,
                                              parent_network_name,
                                              description=None,
                                              is_shared=None):
        """Create a new directly connected org vdc network in this vdc.

        :param str network_name: name of the new network.
        :param str parent_network_name: name of the external network that the
            new network will be directly connected to.
        :param str description: description of the new network.
        :param bool is_shared: True, if the network is shared with other org
            vdc(s) in the organization, else False.

        :return: an object containing EntityType.ORG_VDC_NETWORK XML data which
            represents an org vdc network.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        self.get_resource()

        platform = Platform(self.client)
        parent_network = platform.get_external_network(parent_network_name)
        parent_network_href = parent_network.get('href')

        request_payload = E.OrgVdcNetwork(name=network_name)
        if description is not None:
            request_payload.append(E.Description(description))
        vdc_network_configuration = E.Configuration()
        vdc_network_configuration.append(
            E.ParentNetwork(href=parent_network_href))
        vdc_network_configuration.append(E.FenceMode(FenceMode.BRIDGED.value))
        request_payload.append(vdc_network_configuration)
        if is_shared is not None:
            request_payload.append(E.IsShared(is_shared))

        return self.client.post_linked_resource(
            self.resource, RelationType.ADD, EntityType.ORG_VDC_NETWORK.value,
            request_payload)

    def create_isolated_vdc_network(self,
                                    network_name,
                                    network_cidr,
                                    description=None,
                                    primary_dns_ip=None,
                                    secondary_dns_ip=None,
                                    dns_suffix=None,
                                    ip_range_start=None,
                                    ip_range_end=None,
                                    is_dhcp_enabled=None,
                                    default_lease_time=None,
                                    max_lease_time=None,
                                    dhcp_ip_range_start=None,
                                    dhcp_ip_range_end=None,
                                    is_shared=None):
        """Create a new isolated org vdc network in this vdc.

        :param str network_name: name of the new network.
        :param str network_cidr: CIDR in the format of 10.2.2.1/20.
        :param str description: description of the new network.
        :param str primary_dns_ip: IP address of primary DNS server.
        :param str secondary_dns_ip: IP address of secondary DNS Server.
        :param str dns_suffix: DNS suffix.
        :param str ip_range_start: start address of the IP ranges used for
            static pool allocation in the network.
        :param str ip_range_end: end address of the IP ranges used for static
            pool allocation in the network.
        :param bool is_dhcp_enabled: True, if DHCP service is enabled on the
            new network.
        :param int default_lease_time: default lease in seconds for DHCP
            addresses.
        :param int max_lease_time: max lease in seconds for DHCP addresses.
        :param str dhcp_ip_range_start: start address of the IP range used for
            DHCP addresses.
        :param str dhcp_ip_range_end: end address of the IP range used for DHCP
            addresses.
        :param bool is_shared: True, if the network is shared with other vdc(s)
            in the organization, else False.

        :return: an object containing EntityType.ORG_VDC_NETWORK XML data which
            represents an org vdc network.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        gateway_ip, netmask = cidr_to_netmask(network_cidr)

        self.get_resource()

        request_payload = E.OrgVdcNetwork(name=network_name)
        if description is not None:
            request_payload.append(E.Description(description))

        vdc_network_configuration = E.Configuration()
        ip_scope = E.IpScope()
        ip_scope.append(E.IsInherited('false'))
        ip_scope.append(E.Gateway(gateway_ip))
        ip_scope.append(E.Netmask(netmask))
        if primary_dns_ip is not None:
            ip_scope.append(E.Dns1(primary_dns_ip))
        if secondary_dns_ip is not None:
            ip_scope.append(E.Dns2(secondary_dns_ip))
        if dns_suffix is not None:
            ip_scope.append(E.DnsSuffix(dns_suffix))
        if ip_range_start is not None and ip_range_end is not None:
            ip_range = E.IpRange()
            ip_range.append(E.StartAddress(ip_range_start))
            ip_range.append(E.EndAddress(ip_range_end))
            ip_scope.append(E.IpRanges(ip_range))
        vdc_network_configuration.append(E.IpScopes(ip_scope))
        vdc_network_configuration.append(E.FenceMode(FenceMode.ISOLATED.value))
        request_payload.append(vdc_network_configuration)

        dhcp_service = E.DhcpService()
        if is_dhcp_enabled is not None:
            dhcp_service.append(E.IsEnabled(is_dhcp_enabled))
        if default_lease_time is not None:
            dhcp_service.append(E.DefaultLeaseTime(str(default_lease_time)))
        if max_lease_time is not None:
            dhcp_service.append(E.MaxLeaseTime(str(max_lease_time)))
        if dhcp_ip_range_start is not None and dhcp_ip_range_end is not None:
            dhcp_ip_range = E.IpRange()
            dhcp_ip_range.append(E.StartAddress(dhcp_ip_range_start))
            dhcp_ip_range.append(E.EndAddress(dhcp_ip_range_end))
            dhcp_service.append(dhcp_ip_range)
        request_payload.append(E.ServiceConfig(dhcp_service))

        if is_shared is not None:
            request_payload.append(E.IsShared(is_shared))

        return self.client.post_linked_resource(
            self.resource, RelationType.ADD, EntityType.ORG_VDC_NETWORK.value,
            request_payload)

    def list_orgvdc_network_records(self):
        """Fetch all org vdc network's record in the current vdc.

        :return: org vdc network's name (as key) and admin href (as value)

        :rtype: dict
        """
        # TODO(): We should remove this hack and default to ORG_VDC_NETWORK
        # once vCD 9.0 reaches EOL. We are forced to use OrgNetwork typed
        # query instead of OrgVdcNetwork typed query because for vCD api
        # v29.0 and lower the link for the former is missing from /api/query
        use_hack = False
        if not self.client.is_sysadmin() and\
           float(self.client.get_api_version()) <= 29.0:
            use_hack = True

        if use_hack:
            resource_type = ResourceType.ORG_NETWORK.value
            # OrgNetwork doesn't have a vdc attribute, so the result will
            # contain all org vdc networks in the organization and not just the
            # networks in the current vdc. There is no fix for this!
            vdc_filter = None
        else:
            resource_type = ResourceType.ORG_VDC_NETWORK.value
            vdc_filter = ('vdc', self.href)

        query = self.client.get_typed_query(
            resource_type,
            query_result_format=QueryResultFormat.RECORDS,
            equality_filter=vdc_filter)
        records = query.execute()

        result = {}
        for record in records:
            if use_hack:
                # If the record contains OrgNetworkRecord the href of the
                # network will be non admin one, so we need to change it to
                # its admin version. OrgVdcNetworkRecord contains the admin
                # version of the network href by default.
                result[record.get('name')] = get_admin_href(record.get('href'))
            else:
                result[record.get('name')] = record.get('href')

        return result

    def get_orgvdc_network_admin_href_by_name(self, orgvdc_network_name):
        """Fetch the href of an org vdc network in the current vdc.

        :return: org vdc network admin href

        :rtype: str

        :raises: EntityNotFoundException: if the named org vdc network cannot
            be located.
        """
        records_dict = self.list_orgvdc_network_records()

        # dictionary key presence checks are case sensitive so we need to
        # iterate over the keys and manually check each one of them.
        for net_name in records_dict.keys():
            if orgvdc_network_name.lower() == net_name.lower():
                return records_dict.get(net_name)

        raise EntityNotFoundException(
            "Org vdc network \'%s\' does not exist in vdc \'%s\'" %
            (orgvdc_network_name, self.get_resource().get('name')))

    def list_orgvdc_network_resources(self, name=None, type=None):
        """Fetch org vdc networks filtered by name and type.

        :param str name: name of the network we want to retrieve.
        :param str type: type of network we want to retrieve, valid values
            are 'bridged' and 'isolated'.

        :return: a list of lxml.objectify.ObjectifiedElement objects, where
            each object contains EntityType.ORG_VDC_NETWORK XML data which
            represents an org vdc network.

        :rtype: list
        """
        records_dict = self.list_orgvdc_network_records()
        result = []
        for net_name, net_href in records_dict.items():
            orgvdc_network_resource = self.client.get_resource(net_href)
            if type is not None:
                if hasattr(orgvdc_network_resource, 'Configuration') and \
                   hasattr(orgvdc_network_resource.Configuration, 'FenceMode'):
                    fence_mode = str(
                        orgvdc_network_resource.Configuration.FenceMode)
                    if fence_mode.lower() != type.lower():
                        continue
                else:
                    continue
            if name is not None:
                if orgvdc_network_resource.get('name') != name:
                    continue
            result.append(orgvdc_network_resource)
        return result

    def list_orgvdc_routed_networks(self):
        """Fetch all routed org vdc networks in the current vdc.

        :return: a list of lxml.objectify.ObjectifiedElement objects, where
            each object contains EntityType.ORG_VDC_NETWORK XML data which
            represents an org vdc network.

        :rtype: list
        """
        return self.list_orgvdc_network_resources(
            type=FenceMode.NAT_ROUTED.value)

    def list_orgvdc_direct_networks(self):
        """Fetch all directly connected org vdc networks in the current vdc.

        :return: a list of lxml.objectify.ObjectifiedElement objects, where
            each object contains EntityType.ORG_VDC_NETWORK XML data which
            represents an org vdc network.

        :rtype: list
        """
        return self.list_orgvdc_network_resources(type=FenceMode.BRIDGED.value)

    def list_orgvdc_isolated_networks(self):
        """Fetch all isolated org vdc networks in the current vdc.

        :return: a list of lxml.objectify.ObjectifiedElement objects, where
            each object contains EntityType.ORG_VDC_NETWORK XML data which
            represents an org vdc network.

        :rtype: list
        """
        return self.list_orgvdc_network_resources(
            type=FenceMode.ISOLATED.value)

    def get_routed_orgvdc_network(self, name):
        """Retrieve a routed org vdc network in the current vdc.

        :param str name: name of the org vdc network we want to retrieve.

        :return: an object containing EntityType.ORG_VDC_NETWORK XML data which
            represents an org vdc network.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: EntityNotFoundException: if org vdc network with the given
            name is not found.
        """
        result = self.list_orgvdc_network_resources(
            name=name, type=FenceMode.NAT_ROUTED.value)
        if len(result) == 0:
            raise EntityNotFoundException(
                'Org vdc network with name \'%s\' not found.' % name)
        return result[0]

    def get_direct_orgvdc_network(self, name):
        """Retrieve a directly connected org vdc network in the current vdc.

        :param str name: name of the org vdc network we want to retrieve.

        :return: an object containing EntityType.ORG_VDC_NETWORK XML data which
            represents an org vdc network.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: EntityNotFoundException: if org vdc network with the given
            name is not found.
        """
        result = self.list_orgvdc_network_resources(
            name=name, type=FenceMode.BRIDGED.value)
        if len(result) == 0:
            raise EntityNotFoundException(
                'Org vdc network with name \'%s\' not found.' % name)
        return result[0]

    def get_isolated_orgvdc_network(self, name):
        """Retrieve an isolated org vdc network in the current vdc.

        :param str name: name of the org vdc network we want to retrieve.

        :return: an object containing EntityType.ORG_VDC_NETWORK XML data which
            represents an org vdc network.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: EntityNotFoundException: if org vdc network with the given
            name is not found.
        """
        result = self.list_orgvdc_network_resources(
            name=name, type=FenceMode.ISOLATED.value)
        if len(result) == 0:
            raise EntityNotFoundException(
                'Org vdc network with name \'%s\' not found.' % name)
        return result[0]

    def delete_routed_orgvdc_network(self, name, force=False):
        """Delete a routed org vdc network in the current vdc.

        :param str name: name of the org vdc network we want to delete.
        :param bool force: if True, will instruct vcd to force delete the
            network, ignoring whether it is connected to a vm or vapp network
            or not.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is deleting the network.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: EntityNotFoundException: if org vdc network with the given
            name is not found.
        """
        net_resource = self.get_routed_orgvdc_network(name)
        return self.client.delete_resource(
            net_resource.get('href'), force=force)

    def delete_direct_orgvdc_network(self, name, force=False):
        """Delete a directly connected org vdc network in the current vdc.

        :param str name: name of the org vdc network we want to delete.
        :param bool force: if True, will instruct vcd to force delete the
            network, ignoring whether it is connected to a vm or vapp network
            or not.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is deleting the network.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: EntityNotFoundException: if org vdc network with the given
            name is not found.
        """
        net_resource = self.get_direct_orgvdc_network(name)
        return self.client.delete_resource(
            net_resource.get('href'), force=force)

    def delete_isolated_orgvdc_network(self, name, force=False):
        """Delete an isolated org vdc network in the current vdc.

        :param str name: name of the org vdc network we want to delete.
        :param bool force: if True, will instruct vcd to force delete the
            network, ignoring whether it is connected to a vm or vapp network
            or not.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is deleting the network.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: EntityNotFoundException: if org vdc network with the given
            name is not found.
        """
        net_resource = self.get_isolated_orgvdc_network(name)
        return self.client.delete_resource(
            net_resource.get('href'), force=force)

    def create_gateway_api_version_32(
            self,
            name,
            external_networks=None,
            gateway_backing_config=GatewayBackingConfigType.COMPACT.value,
            desc=None,
            is_default_gateway=False,
            selected_extnw_for_default_gw=None,
            default_gateway_ip=None,
            is_default_gw_for_dns_relay_selected=False,
            is_ha_enabled=False,
            should_create_as_advanced=False,
            is_dr_enabled=False,
            is_ip_settings_configured=False,
            ext_net_to_participated_subnet_with_ip_settings=None,
            is_sub_allocate_ip_pools_enabled=False,
            ext_net_to_subnet_with_ip_range=None,
            ext_net_to_rate_limit=None,
            is_flips_mode_enabled=False,
            edgeGatewayType=EdgeGatewayType.NSXV_BACKED.value):
        """Request the creation of a gateway.

        :param str name: name of the new gateway.
        :param list external_networks: list of external network's name to
        which gateway can connect.
        :param str gateway_backing_config: gateway backing config. Possible
        values can be compact/full/full4/x-large.
        :param str desc: description of the new gateway
        :param bool is_default_gateway: should the new gateway be configured as
         the default gateway.
        :param str selected_extnw_for_default_gw: selected external network
        for default gateway.
        :param str default_gateway_ip: selected dafault gateway IP
        :param bool is_default_gw_for_dns_relay_selected: is default gateway
         for dns relay selected
        :param bool is_ha_enabled: is HA enabled
        :param bool should_create_as_advanced: create as advanced gateway
        :param bool is_dr_enabled: is distributed routing enabled
        :param bool is_ip_settings_configured: is ip settings configured
        :param dict ext_net_to_participated_subnet_with_ip_settings:
        external network to subnet ip with ip assigned in case of manual
        else Auto e.g., {"ext_net' : {'10.3.2.1/24' : Auto/10.3.2.2}}
        :param bool is_sub_allocate_ip_pools_enabled: is sub allocate ip
        pools enabled
        :param dict ext_net_to_subnet_with_ip_range: external network to sub
        allocated ip with ip ranges e.g., {"ext_net' : {'10.3.2.1/24' : [
        10.3.2.2-10.3.2.5, 10.3.2.12-10.3.2.15]}}
        :param dict ext_net_to_rate_limit: external network to rate limit
        e.g., {'ext_net' : {100 : 100}}
        :param bool is_flips_mode_enabled: is flip mode enabled
        :param str edgeGatewayType: edge gateway type. possible values will
        be NSXV_BACKED/NSXT_BACKED/NSXT_IMPORTED

        :return: an object containing EntityType.GATEWAY XML data which
        represents the new gateway being created along with the the
        asynchronous task that is creating the gateway.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if external_networks is None or len(external_networks) == 0:
            raise InvalidParameterException('external networks can not be '
                                            'Null.')
        resource_admin = self.client.get_resource(self.href_admin)

        gateway_params = E.EdgeGateway(name=name)
        if desc is not None:
            gateway_params.append(E.Description(desc))
        gateway_configuration_param = \
            self._create_gateway_configuration_param(
                external_networks, gateway_backing_config,
                is_default_gateway, selected_extnw_for_default_gw,
                default_gateway_ip, is_default_gw_for_dns_relay_selected,
                is_ha_enabled, should_create_as_advanced, is_dr_enabled,
                is_ip_settings_configured,
                ext_net_to_participated_subnet_with_ip_settings,
                is_sub_allocate_ip_pools_enabled,
                ext_net_to_subnet_with_ip_range, ext_net_to_rate_limit)
        gateway_configuration_param.append(
            E.FipsModeEnabled(is_flips_mode_enabled))
        gateway_configuration_param.append(E.EdgeGatewayType(edgeGatewayType))

        gateway_params.append(gateway_configuration_param)
        return self.client.post_linked_resource(
            resource_admin, RelationType.ADD, EntityType.EDGE_GATEWAY.value,
            gateway_params)

    def create_gateway_api_version_30(
            self,
            name,
            external_networks=None,
            gateway_backing_config=GatewayBackingConfigType.COMPACT.value,
            desc=None,
            is_default_gateway=False,
            selected_extnw_for_default_gw=None,
            default_gateway_ip=None,
            is_default_gw_for_dns_relay_selected=False,
            is_ha_enabled=False,
            should_create_as_advanced=False,
            is_dr_enabled=False,
            is_ip_settings_configured=False,
            ext_net_to_participated_subnet_with_ip_settings=None,
            is_sub_allocate_ip_pools_enabled=False,
            ext_net_to_subnet_with_ip_range=None,
            ext_net_to_rate_limit=None):
        """Request the creation of a gateway for API version 30 or lower.

        :param str name: name of the new gateway.
        :param list external_networks: list of external network's name to
        which gateway can connect.
        :param str gateway_backing_config: gateway backing config. Possible
        values can be compact/full/full4/x-large.
        :param str desc: description of the new gateway
        :param bool is_default_gateway: should the new gateway be configured as
         the default gateway.
        :param str selected_extnw_for_default_gw: selected external network
        for default gateway.
        :param str default_gateway_ip: selected dafault gateway IP
        :param bool is_default_gw_for_dns_relay_selected: is default gateway
         for dns relay selected
        :param bool is_ha_enabled: is HA enabled
        :param bool should_create_as_advanced: create as advanced gateway
        :param bool is_dr_enabled: is distributed routing enabled
        :param bool is_ip_settings_configured: is ip settings configured
        :param dict ext_net_to_participated_subnet_with_ip_settings:
        external network to subnet ip with ip assigned in case of manual
        else Auto e.g., {"ext_net' : {'10.3.2.1/24' : Auto/10.3.2.2}}
        :param bool is_sub_allocate_ip_pools_enabled: is sub allocate ip
        pools enabled
        :param dict ext_net_to_subnet_with_ip_range: external network to sub
        allocated ip with ip ranges e.g., {"ext_net' : {'10.3.2.1/24' : [
        10.3.2.2-10.3.2.5, 10.3.2.12-10.3.2.15]}}
        :param dict ext_net_to_rate_limit: external network to rate limit
        e.g., {'ext_net' : {100 : 100}}

        :return: an object containing EntityType.GATEWAY XML data which
        represents the new gateway being created along with the the
        asynchronous task that is creating the gateway.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if external_networks is None or len(external_networks) == 0:
            raise InvalidParameterException('external networks can not be '
                                            'Null.')

        resource_admin = self.client.get_resource(self.href_admin)
        gateway_params = E.EdgeGateway(name=name)
        if desc is not None:
            gateway_params.append(E.Description(desc))

        gateway_configuration_param = \
            self._create_gateway_configuration_param(
                external_networks, gateway_backing_config,
                is_default_gateway, selected_extnw_for_default_gw,
                default_gateway_ip, is_default_gw_for_dns_relay_selected,
                is_ha_enabled, should_create_as_advanced, is_dr_enabled,
                is_ip_settings_configured,
                ext_net_to_participated_subnet_with_ip_settings,
                is_sub_allocate_ip_pools_enabled,
                ext_net_to_subnet_with_ip_range, ext_net_to_rate_limit)
        gateway_params.append(gateway_configuration_param)

        return self.client.post_linked_resource(
            resource_admin, RelationType.ADD, EntityType.EDGE_GATEWAY.value,
            gateway_params)

    def create_gateway_api_version_31(
            self,
            name,
            external_networks=None,
            gateway_backing_config=GatewayBackingConfigType.COMPACT.value,
            desc=None,
            is_default_gateway=False,
            selected_extnw_for_default_gw=None,
            default_gateway_ip=None,
            is_default_gw_for_dns_relay_selected=False,
            is_ha_enabled=False,
            should_create_as_advanced=False,
            is_dr_enabled=False,
            is_ip_settings_configured=False,
            ext_net_to_participated_subnet_with_ip_settings=None,
            is_sub_allocate_ip_pools_enabled=False,
            ext_net_to_subnet_with_ip_range=None,
            ext_net_to_rate_limit=None,
            is_flips_mode_enabled=False):
        """Request the creation of a gateway.

        :param str name: name of the new gateway.
        :param list external_networks: list of external network's name to
        which gateway can connect.
        :param str gateway_backing_config: gateway backing config. Possible
        values can be compact/full/full4/x-large.
        :param str desc: description of the new gateway
        :param bool is_default_gateway: should the new gateway be configured as
         the default gateway.
        :param str selected_extnw_for_default_gw: selected external network
        for default gateway.
        :param str default_gateway_ip: selected dafault gateway IP
        :param bool is_default_gw_for_dns_relay_selected: is default gateway
         for dns relay selected
        :param bool is_ha_enabled: is HA enabled
        :param bool should_create_as_advanced: create as advanced gateway
        :param bool is_dr_enabled: is distributed routing enabled
        :param bool is_ip_settings_configured: is ip settings configured
        :param dict ext_net_to_participated_subnet_with_ip_settings:
        external network to subnet ip with ip assigned in case of manual
        else Auto e.g., {"ext_net' : {'10.3.2.1/24' : Auto/10.3.2.2}}
        :param bool is_sub_allocate_ip_pools_enabled: is sub allocate ip
        pools enabled
        :param dict ext_net_to_subnet_with_ip_range: external network to sub
        allocated ip with ip ranges e.g., {"ext_net' : {'10.3.2.1/24' : [
        10.3.2.2-10.3.2.5, 10.3.2.12-10.3.2.15]}}
        :param dict ext_net_to_rate_limit: external network to rate limit
        e.g., {'ext_net' : {100 : 100}}
        :param bool is_flips_mode_enabled: is flip mode enabled

        :return: an object containing EntityType.GATEWAY XML data which
        represents the new gateway being created along with the the
        asynchronous task that is creating the gateway.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if external_networks is None or len(external_networks) == 0:
            raise InvalidParameterException('external networks can not be '
                                            'Null.')
        resource_admin = self.client.get_resource(self.href_admin)

        gateway_params = E.EdgeGateway(name=name)
        if desc is not None:
            gateway_params.append(E.Description(desc))
        gateway_configuration_param = \
            self._create_gateway_configuration_param(
                external_networks, gateway_backing_config,
                is_default_gateway, selected_extnw_for_default_gw,
                default_gateway_ip, is_default_gw_for_dns_relay_selected,
                is_ha_enabled, should_create_as_advanced, is_dr_enabled,
                is_ip_settings_configured,
                ext_net_to_participated_subnet_with_ip_settings,
                is_sub_allocate_ip_pools_enabled,
                ext_net_to_subnet_with_ip_range, ext_net_to_rate_limit)
        gateway_configuration_param.append(
            E.FipsModeEnabled(is_flips_mode_enabled))
        gateway_params.append(gateway_configuration_param)

        return self.client.post_linked_resource(
            resource_admin, RelationType.ADD, EntityType.EDGE_GATEWAY.value,
            gateway_params)

    def _create_gateway_configuration_param(
            self,
            external_networks,
            gateway_backing_config,
            is_default_gateway=False,
            selected_extnw_for_default_gw=None,
            default_gateway_ip=None,
            is_default_gw_for_dns_relay_selected=False,
            is_ha_enabled=False,
            should_create_as_advanced=False,
            is_dr_enabled=False,
            is_ip_settings_configured=False,
            ext_net_to_participated_subnet_with_ip_settings=None,
            is_sub_allocate_ip_pools_enabled=False,
            ext_net_to_subnet_with_ip_range=None,
            ext_net_to_rate_limit=None):
        """Create gateway configuration param.

        :return: gateway configuration param

        :rtype: lxml.objectify.ObjectifiedElement
        """
        platform = Platform(self.client)
        provided_networks_resource = []
        for ext_net_name in external_networks:
            ext_network = platform.get_external_network(ext_net_name)
            provided_networks_resource.append(ext_network)
        gateway_configuration_param = E.Configuration()
        gateway_configuration_param.append(
            E.GatewayBackingConfig(gateway_backing_config))
        # Creating gateway interfaces
        gateway_interfaces_param = E.GatewayInterfaces()
        # Creating gateway interface
        for ext_net in provided_networks_resource:
            ext_net_resource = self.client.get_resource(ext_net.get('href'))
            gateway_interface_param = E.GatewayInterface()
            gateway_interface_param.append(E.Name(ext_net.get('name')))
            gateway_interface_param.append(E.DisplayName(ext_net.get('name')))
            gateway_interface_param.append(E.Network(href=ext_net.get('href')))
            gateway_interface_param.append(E.InterfaceType('uplink'))
            # Add subnet participation
            ip_scopes = ext_net_resource.xpath(
                'vcloud:Configuration/vcloud:IpScopes/vcloud:IpScope',
                namespaces=NSMAP)
            for ip_scope in ip_scopes:
                prefix_len = netmask_to_cidr_prefix_len(
                    ip_scope.Gateway.text, ip_scope.Netmask.text)

                subnet_participation_param = E.SubnetParticipation()
                is_ip_scope_participating = False
                is_default_gw_configured = False
                ip_range_provided = False
                # Configure Default Gateway
                if is_default_gateway is True and (
                        ext_net.get('name') == selected_extnw_for_default_gw
                ) and ip_scope.Gateway == default_gateway_ip:
                    subnet_participation_param.append(
                        E.Gateway(ip_scope.Gateway.text))
                    subnet_participation_param.append(
                        E.Netmask(ip_scope.Netmask.text))
                    is_default_gw_configured = True
                # Configure Ip Settings
                if is_ip_settings_configured is True and \
                        ext_net_to_participated_subnet_with_ip_settings is \
                        not None and len(
                        ext_net_to_participated_subnet_with_ip_settings) > 0:
                    subnet_with_ip_settings = \
                        ext_net_to_participated_subnet_with_ip_settings.get(
                            ext_net.get('name'))
                    if subnet_with_ip_settings is not None and \
                            len(subnet_with_ip_settings) > 0:
                        for subnet in subnet_with_ip_settings \
                                .keys():
                            subnet_arr = subnet.split('/')
                            if len(subnet_arr) < 2:
                                continue
                            if subnet_arr[0] == ip_scope.Gateway.text and \
                                    subnet_arr[1] == prefix_len:
                                ip_assigned = \
                                    subnet_with_ip_settings.get(subnet)
                                if len(ip_assigned) > 0:
                                    is_ip_scope_participating = True
                                    if is_default_gw_configured is False:
                                        subnet_participation_param.append(
                                            E.Gateway(ip_scope.Gateway.text))
                                        subnet_participation_param.append(
                                            E.Netmask(ip_scope.Netmask.text))

                                    if ip_assigned != 'Auto':
                                        subnet_participation_param.append(
                                            E.IpAddress(ip_assigned))
                # Configure Sub Allocated Ips
                if is_sub_allocate_ip_pools_enabled is True and \
                        ext_net_to_subnet_with_ip_range is not None and len(
                        ext_net_to_subnet_with_ip_range) > 0:
                    subnet_with_ip_ranges = ext_net_to_subnet_with_ip_range \
                        .get(ext_net.get('name'))
                    if subnet_with_ip_ranges is not None and len(
                            subnet_with_ip_ranges) > 0:
                        for subnet in subnet_with_ip_ranges.keys():
                            subnet_arr = subnet.split('/')
                            if len(subnet_arr) < 2:
                                continue
                            if subnet_arr[0] == ip_scope.Gateway.text and \
                                    subnet_arr[1] == prefix_len:
                                ip_ranges = subnet_with_ip_ranges.get(subnet)
                                if is_default_gw_configured is False and \
                                        is_ip_scope_participating is False:
                                    subnet_participation_param.append(
                                        E.Gateway(ip_scope.Gateway.text))
                                    subnet_participation_param.append(
                                        E.Netmask(ip_scope.Netmask.text))

                                ip_ranges_param = E.IpRanges()

                                for ip_range in ip_ranges:
                                    ip_range_arr = ip_range.split('-')
                                    ip_range_param = E.IpRange()
                                    ip_range_param.append(
                                        E.StartAddress(ip_range_arr[0]))
                                    ip_range_param.append(
                                        E.EndAddress(ip_range_arr[1]))
                                    ip_ranges_param.append(ip_range_param)
                                    ip_range_provided = True
                                if ip_range_provided is True:
                                    subnet_participation_param.append(
                                        ip_ranges_param)

                if is_default_gw_configured is True:
                    subnet_participation_param.append(
                        E.UseForDefaultRoute(True))
                if is_ip_scope_participating is True or \
                        is_default_gw_configured is True or \
                        ip_range_provided is True:
                    gateway_interface_param.append(subnet_participation_param)
            # Configure Rate Limit
            if ext_net_to_rate_limit is not None and len(
                    ext_net_to_rate_limit) > 0:
                rate_limit = ext_net_to_rate_limit.get(ext_net.get('name'))
                if rate_limit is not None and len(rate_limit) > 0:
                    gateway_interface_param.append(E.ApplyRateLimit(True))
                    for key in rate_limit.keys():
                        gateway_interface_param.append(E.InRateLimit(key))
                        gateway_interface_param.append(
                            E.OutRateLimit(rate_limit.get(key)))

            # Add to the Interfaces
            gateway_interfaces_param.append(gateway_interface_param)

        gateway_configuration_param.append(gateway_interfaces_param)
        gateway_configuration_param.append(E.HaEnabled(is_ha_enabled))
        if is_default_gateway is True:
            gateway_configuration_param.append(
                E.UseDefaultRouteForDnsRelay(
                    is_default_gw_for_dns_relay_selected))
        syslog_server_settings = E.SyslogServerSettings()
        syslog_server_settings.append(E.TenantSyslogServerSettings())
        gateway_configuration_param.append(syslog_server_settings)
        gateway_configuration_param.append(
            E.AdvancedNetworkingEnabled(should_create_as_advanced))
        gateway_configuration_param.append(
            E.DistributedRoutingEnabled(is_dr_enabled))
        return gateway_configuration_param

    def delete_gateway(self, name):
        """Delete a gateway in the current org vdc.

        :param str name: name of the gateway to be deleted.

        :raises: EntityNotFoundException: if the named gateway can not be
         found.
        """
        name_filter = ('name', name)
        query = self.client.get_typed_query(
            ResourceType.EDGE_GATEWAY.value,
            query_result_format=QueryResultFormat.RECORDS,
            equality_filter=name_filter)
        records = query.execute()
        if records is None:
            raise EntityNotFoundException(
                'Gateway with name \'%s\' not found for delete.' % name)
        href = None
        for record in records:
            href = record.get('href')
            break

        return self.client.delete_resource(href)

    def get_gateway(self, name):
        """Get a gateway in the current org vdc.

        :param str name: name of the gateway to be fetched.

        :return: gateway

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: EntityNotFoundException: if the named gateway can not be
        found.
        :raises: MultipleRecordsException: if more than one gateway with the
            provided name are found.
        """
        name_filter = ('name', name)
        query = self.client.get_typed_query(
            ResourceType.EDGE_GATEWAY.value,
            query_result_format=QueryResultFormat.RECORDS,
            equality_filter=name_filter)
        records = list(query.execute())
        if records is None or len(records) == 0:
            return None
        elif len(records) > 1:
            raise MultipleRecordsException("Found multiple gateway named "
                                           "'%s'," % name)
        return records[0]
