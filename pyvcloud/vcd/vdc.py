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

from lxml import etree
from pyvcloud.vcd.client import E
from pyvcloud.vcd.client import E_OVF
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import find_link
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.org import Org


class VDC(object):

    def __init__(self, client, name=None, href=None, resource=None):
        self.client = client
        self.name = name
        self.href = href
        self.resource = resource
        if resource is not None:
            self.name = resource.get('name')
            self.href = resource.get('href')

    def get_resource(self):
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        return self.resource

    def get_resource_href(self, name, entity_type=EntityType.VAPP):
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        result = []
        if hasattr(self.resource, 'ResourceEntities') and \
           hasattr(self.resource.ResourceEntities, 'ResourceEntity'):
            for vapp in self.resource.ResourceEntities.ResourceEntity:
                if entity_type is None or \
                   entity_type.value == vapp.get('type'):
                    if vapp.get('name') == name:
                        result.append(vapp.get('href'))
        if len(result) == 0:
            raise Exception('not found')
        elif len(result) > 1:
            raise Exception('more than one found, use the vapp-id')
        return result[0]

    def reload(self):
        self.resource = self.client.get_resource(self.href)
        if self.resource is not None:
            self.name = self.resource.get('name')
            self.href = self.resource.get('href')

    def get_vapp(self, name):
        return self.client.get_resource(self.get_resource_href(name))

    def delete_vapp(self, name, force=False):
        href = self.get_resource_href(name)
        return self.client.delete_resource(href, force)

    def instantiate_vapp(self,
                         name,
                         catalog,
                         template,
                         network=None,
                         fence_mode='bridged',
                         ip_allocation_mode='dhcp',
                         deploy=True,
                         power_on=True,
                         accept_all_eulas=True,
                         memory=None,
                         cpu=None,
                         password=None,
                         cust_script=None,
                         identical=False):
        """
        Instantiate a vApp from a vApp template.
        :param name: (str): The name of the new vApp.
        :param catalog: (str): The name of the catalog.
        :param template: (str): The name of the vApp template.
        :param identical: (bool): If True, no guest customization or VM name update is performed
        :return:  A :class:`lxml.objectify.StringElement` object describing the new vApp.
        """  # NOQA
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        network_href = None
        if hasattr(self.resource, 'AvailableNetworks') and \
           hasattr(self.resource.AvailableNetworks, 'Network'):
            for n in self.resource.AvailableNetworks.Network:
                if network is None or network == n.get('name'):
                    network_href = n.get('href')
                    network_name = n.get('name')
        if network_href is None:
            raise Exception('Network not found in the Virtual Datacenter.')
        org_href = find_link(self.resource,
                             RelationType.UP,
                             EntityType.ORG.value).href
        org = Org(self.client, href=org_href)
        template_resource = org.get_catalog_item(catalog, template)
        v = self.client.get_resource(template_resource.Entity.get('href'))
        n = v.xpath(
            '//ovf:NetworkSection/ovf:Network',
            namespaces={'ovf': 'http://schemas.dmtf.org/ovf/envelope/1'})
        assert len(n) > 0
        network_name_from_template = n[0].get(
            '{http://schemas.dmtf.org/ovf/envelope/1}name')
        deploy_param = 'true' if deploy else 'false'
        power_on_param = 'true' if power_on else 'false'
        network_configuration = E.Configuration(
            E.ParentNetwork(href=network_href),
            E.FenceMode(fence_mode)
        )
        # if fence_mode == 'natRouted':
        #     network_configuration.append(
        #         E.Features(
        #             E.NatService(
        #                 E.IsEnabled('true'),
        #                 E.NatType('ipTranslation'),
        #                 E.Policy('allowTraffic'),
        #                 E.NatRule(
        #                     E.OneToOneVmRule(
        #                         E.MappingMode('automatic'),
        #                         E.VAppScopedVmId(vm_id),
        #                         E.VmNicId(0)
        #                     )
        #                 )
        #             )
        #         )
        #     )
        vapp_network_name = network_name_from_template
        if vapp_network_name == 'none':
            vapp_network_name = network_name
        vapp_template_params = E.InstantiateVAppTemplateParams(
            name=name,
            deploy=deploy_param,
            powerOn=power_on_param)
        if network_name is not None:
            vapp_template_params.append(
                E.InstantiationParams(
                    E.NetworkConfigSection(
                        E_OVF.Info('Configuration for logical networks'),
                        E.NetworkConfig(
                            network_configuration,
                            networkName=vapp_network_name
                        )
                    )
                )
            )
        vapp_template_params.append(
            E.Source(href=template_resource.Entity.get('href'))
        )
        vm = v.xpath(
            '//vcloud:VAppTemplate/vcloud:Children/vcloud:Vm',
            namespaces=NSMAP)
        assert len(vm) > 0
        ip = E.InstantiationParams()
        if not identical:
            gc = E.GuestCustomizationSection(
                E_OVF.Info('Specifies Guest OS Customization Settings'),
                E.Enabled('false'),
            )
            if password is not None:
                gc.append(E.AdminPasswordEnabled('true'))
                gc.append(E.AdminPasswordAuto('false'))
                gc.append(E.AdminPassword(password))
                gc.append(E.ResetPasswordRequired('false'))
            else:
                gc.append(E.AdminPasswordEnabled('false'))
            if cust_script is not None:
                gc.append(E.CustomizationScript(cust_script))
            gc.Enabled = E.Enabled('true')
            gc.append(E.ComputerName(name))
            ip.append(gc)
        primary_index = int(
            vm[0].NetworkConnectionSection.PrimaryNetworkConnectionIndex.text)
        ip.append(E.NetworkConnectionSection(
                E_OVF.Info('Specifies the available VM network connections'),
                E.NetworkConnection(
                    E.NetworkConnectionIndex(primary_index),
                    E.IsConnected('true'),
                    E.IpAddressAllocationMode(ip_allocation_mode.upper()),
                    network=vapp_network_name
                )
            ))
        if memory is not None:
            items = v.Children[0].Vm.xpath(
                '//ovf:VirtualHardwareSection/ovf:Item',
                namespaces={'ovf': 'http://schemas.dmtf.org/ovf/envelope/1'})
            for item in items:
                if item['{http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData}ResourceType'] == 4:  # NOQA
                    item['{http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData}ElementName'] = '%s MB of memory' % memory # NOQA
                    item['{http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData}VirtualQuantity'] = memory # NOQA
                    memory_params = item
                    break
        if cpu is not None:
            items = v.Children[0].Vm.xpath(
                '//ovf:VirtualHardwareSection/ovf:Item',
                namespaces={'ovf': 'http://schemas.dmtf.org/ovf/envelope/1'})
            for item in items:
                if item['{http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData}ResourceType'] == 3:  # NOQA
                    item['{http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData}ElementName'] = '%s virtual CPU(s)' % cpu # NOQA
                    item['{http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData}VirtualQuantity'] = cpu # NOQA
                    cpu_params = item
                    break

        if memory is not None or cpu is not None:
            vhs = E_OVF.VirtualHardwareSection(
                E_OVF.Info('Virtual hardware requirements')
            )
            if memory is not None:
                vhs.append(memory_params)
            if cpu is not None:
                vhs.append(cpu_params)
            ip.append(vhs)

        if identical or (password is None and cust_script is None):
            needs_customization = 'false'
        else:
            needs_customization = 'true'
        si = E.SourcedItem(
            E.Source(href=vm[0].get('href'),
                     id=vm[0].get('id'),
                     name=vm[0].get('name'),
                     type=vm[0].get('type'))
        )
        if not identical:
            si.append(E.VmGeneralParams(
                        E.Name(name),
                        E.NeedsCustomization(needs_customization)))
        si.append(ip)
        # if network_name != network_name_from_template:
        #     si.append(E.NetworkAssignment(
        #         innerNetwork=network_name_from_template,
        #         containerNetwork=network_name))
        vapp_template_params.append(si)
        all_eulas_accepted = 'true' if accept_all_eulas else 'false'
        vapp_template_params.append(E.AllEULAsAccepted(all_eulas_accepted))
        return self.client.post_resource(
            self.href+'/action/instantiateVAppTemplate',
            vapp_template_params,
            EntityType.INSTANTIATE_VAPP_TEMPLATE_PARAMS.value)

    def list_resources(self, entity_type=None):
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        result = []
        if hasattr(self.resource, 'ResourceEntities') and \
           hasattr(self.resource.ResourceEntities, 'ResourceEntity'):
            for vapp in self.resource.ResourceEntities.ResourceEntity:
                if entity_type is None or \
                   entity_type.value == vapp.get('type'):
                    result.append({'name': vapp.get('name')})
        return result

    def add_disk(self,
                 name,
                 size,
                 bus_type=None,
                 bus_sub_type=None,
                 description=None,
                 storage_profile_name=None):
        """
        Request the creation of an indendent disk.
        :param name: (str): The name of the new Disk.
        :param size: (str): The size of the new disk in MB.
        :param bus_type: (str): The bus type of the new disk.
        :param bus_subtype: (str): The bus subtype  of the new disk.
        :param description: (str): A description of the new disk.
        :param storage_profile_name: (str): The name of an existing storage profile to be used by the new disk.
        :return:  A :class:`lxml.objectify.StringElement` object describing the asynchronous Task creating the disk.
        """  # NOQA
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)

        diskParms = E.DiskCreateParams(E.Disk(name=name, size=size))

        if description is not None:
            diskParms.Disk.append(E.Description(description))

        if bus_type is not None and bus_sub_type is not None:
            diskParms.Disk.attrib['busType'] = bus_type
            diskParms.Disk.attrib['busSubType'] = bus_sub_type

        if storage_profile_name is not None:
            storage_profile = self.get_storage_profile(storage_profile_name)
            print(etree.tostring(storage_profile, pretty_print=True))
            diskParms.Disk.append(storage_profile)
            # etree.SubElement(diskParms.Disk, 'StorageProfile')
            # diskParms.Disk.append(
            # E.StorageProfile(name=storage_profile_name))
            # diskParms.Disk.StorageProfile.attrib['href'] =
            # storage_profile.get('href')
            # diskParms.Disk.StorageProfile.attrib['name'] =
            # storage_profile.get('name')
            # diskParms.Disk.StorageProfile.attrib['type'] =
            # storage_profile.get('type')

            print(etree.tostring(diskParms, pretty_print=True))

        return self.client.post_linked_resource(
            self.resource,
            RelationType.ADD,
            EntityType.DISK_CREATE_PARMS.value,
            diskParms)

    def update_disk(self, name, size, new_name=None, description=None,
                    disk_id=None):
        """
        Update an existing independent disk.
        :param name: (str): The existing name of the Disk.
        :param new_name: (str): The new name for the Disk.
        :param size: (str): The size of the new disk in MB.
        :param description: (str): A description of the new disk.
        :param description: (str): The disk_id of the existing disk.
        :return:  A :class:`lxml.objectify.StringElement` object describing the asynchronous Task creating the disk.
        """  # NOQA
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)

        diskParms = E.Disk(name=name, size=size)

        if description is not None:
            diskParms.append(E.Description(description))

        if disk_id is not None:
            disk = self.get_disk(None, disk_id)
        else:
            disk = self.get_disk(name)

        if disk is None:
            raise Exception('Could not locate Disk %s for update. ' % disk_id)

        return self.client.put_linked_resource(disk,
                                               RelationType.EDIT,
                                               EntityType.DISK.value,
                                               diskParms)

    def delete_disk(self, name, disk_id=None):
        """
        Delete an existing independent disk.
        :param name: (str): The name of the Disk to delete.
        :param disk_id: (str): The id of the disk to delete.
        :param description: (str): The id of the existing disk.
        :return:  A :class:`lxml.objectify.StringElement` object describing the asynchronous Task creating the disk.
        """  # NOQA
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)

        if disk_id is not None:
            disk = self.get_disk(None, disk_id)
        else:
            disk = self.get_disk(name)

        return self.client.delete_linked_resource(disk,
                                                  RelationType.REMOVE,
                                                  None)

    def get_disks(self):
        """
        Request a list of independent disks defined in a vdc.
        :return: An array of :class:`lxml.objectify.StringElement` objects describing the existing Disks.
        """  # NOQA

        if self.resource is None:
            self.resource = self.client.get_resource(self.href)

        disks = []
        if hasattr(self.resource, 'ResourceEntities') and \
           hasattr(self.resource.ResourceEntities, 'ResourceEntity'):
            for resourceEntity in \
                    self.resource.ResourceEntities.ResourceEntity:

                if resourceEntity.get('type') == \
                   "application/vnd.vmware.vcloud.disk+xml":
                    disk = self.client.get_resource(resourceEntity.get('href'))
                    disks.append(disk)
        return disks

    def get_disk(self, name, disk_id=None):
        """
        Return information for an independent disk.
        :param name: (str): The name of the disk.
        :param disk_id: (str): The id of the disk.
        :return: (list of tuples of (DiskType, list of str)):  An list of tuples. \
                  Each tuple contains a :class:`pyvcloud.schema.vcd.v1_5.schemas.vcloud.diskType.DiskType` object and a list of vms utilizing the disk.
        **service type:** ondemand, subscription, vcd
        """  # NOQA

        if self.resource is None:
            self.resource = self.client.get_resource(self.href)

        disks = self.get_disks()

        if disk_id is not None:
            if not disk_id.startswith('urn:vcloud:disk:'):
                disk_id = 'urn:vcloud:disk:' + disk_id
            for disk in disks:
                if disk.get('id') == disk_id:
                        return disk
        else:
            if name is not None:
                for disk in disks:
                    if name is not None and disk.get('name') == name:
                            return disk
        return None

    def get_storage_profiles(self):
        """
        Request a list of the Storage Profiles defined in a Virtual Data Center.
        :return: An array of :class:`lxml.objectify.StringElement` objects describing the existing Storage Profiles.
        """  # NOQA
        profile_list = []
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)

        if hasattr(self.resource, 'VdcStorageProfiles') and \
           hasattr(self.resource.VdcStorageProfiles, 'VdcStorageProfile'):
            for profile in self.resource.VdcStorageProfiles.VdcStorageProfile:
                profile_list.append(profile)
                return profile_list
        return None

    def get_storage_profile(self, profile_name):
        """
        Request a specific Storage Profile within a Virtual Data Center.
        :param profile_name: (str): The name of the requested storage profile.
        :return: (VdcStorageProfileType)  A :class:`lxml.objectify.StringElement` object describing the requested storage profile.
        """  # NOQA
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)

        if hasattr(self.resource, 'VdcStorageProfiles') and \
           hasattr(self.resource.VdcStorageProfiles, 'VdcStorageProfile'):
            print("Profiles: " + str(etree.tostring(
                self.resource.VdcStorageProfiles, pretty_print=True), "utf-8"))
            for profile in self.resource.VdcStorageProfiles.VdcStorageProfile:
                print("Profile: %s" % profile.get('name'))
                if profile.get('name') == profile_name:
                    return profile

        raise Exception('Storage Profile named \'%s\' not found' %
                        profile_name)
