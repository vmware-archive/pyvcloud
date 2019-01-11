# VMware vCloud Python SDK
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

from ipaddress import IPv4Network
from os.path import abspath
from os.path import dirname
from os.path import join as joinpath
from os.path import realpath

import humanfriendly
from lxml import etree
from lxml.objectify import NoneElement
from pygments import formatters
from pygments import highlight
from pygments import lexers

from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import get_links
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import VCLOUD_STATUS_MAP


def extract_id(urn):
    """Extract id from an urn.

    'urn:vcloud:catalog:39867ab4-04e0-4b13-b468-08abcc1de810' will produce
    '39867ab4-04e0-4b13-b468-08abcc1de810'

    :param str urn: a vcloud resource urn.

    :return: the extracted id

    :rtype: str
    """
    if urn is None:
        return None
    if ':' in urn:
        return urn.split(':')[-1]
    else:
        return urn


def org_to_dict(org):
    """Convert a lxml.objectify.ObjectifiedElement org object to a dict.

    :param lxml.objectify.ObjectifiedElement org: an object containing
        EntityType.ORG or EntityType.ADMIN_ORG XML data.

    :return: dictionary representation of the org.

    :rtype: dict
    """
    result = {}
    result['name'] = org.get('name')
    result['id'] = extract_id(org.get('id'))
    result['full_name'] = str('%s' % org.FullName)
    result['description'] = str('%s' % org.Description)
    result['vdcs'] = [
        str(n.name) for n in get_links(org, media_type=EntityType.VDC.value)
    ]
    result['org_networks'] = [
        str(n.name)
        for n in get_links(org, media_type=EntityType.ORG_NETWORK.value)
    ]
    result['catalogs'] = [
        str(n.name)
        for n in get_links(org, media_type=EntityType.CATALOG.value)
    ]
    return result


def vdc_to_dict(vdc, access_control_settings=None):
    """Convert a lxml.objectify.ObjectifiedElement org vdc object to a dict.

    :param lxml.objectify.ObjectifiedElement vdc: an object containing
        EntityType.VDC XML data.
    :param lxml.objectify.ObjectifiedElement access_control_settings: an object
        containing EntityType.CONTROL_ACCESS_PARAMS XML data.

    :return: dictionary representation of the org vdc.

    :rtype: dict
    """
    result = {}
    result['name'] = vdc.get('name')
    result['id'] = extract_id(vdc.get('id'))
    if hasattr(vdc, 'IsEnabled'):
        result['is_enabled'] = bool(vdc.IsEnabled)
    if hasattr(vdc, 'AvailableNetworks') and \
            hasattr(vdc.AvailableNetworks, 'Network'):
        result['networks'] = []
        for n in vdc.AvailableNetworks.Network:
            result['networks'].append(n.get('name'))
    if hasattr(vdc, 'ComputeCapacity'):
        result['cpu_capacity'] = {
            'units': str(vdc.ComputeCapacity.Cpu.Units),
            'allocated': str(vdc.ComputeCapacity.Cpu.Allocated),
            'limit': str(vdc.ComputeCapacity.Cpu.Limit),
            'reserved': str(vdc.ComputeCapacity.Cpu.Reserved),
            'used': str(vdc.ComputeCapacity.Cpu.Used)
        }
        if hasattr(vdc.ComputeCapacity.Cpu, 'Overhead'):
            result['cpu_capacity'] = str(vdc.ComputeCapacity.Cpu.Overhead)
        result['mem_capacity'] = {
            'units':
            str(vdc.ComputeCapacity.Memory.Units),
            'allocated':
            str(vdc.ComputeCapacity.Memory.Allocated),
            'limit':
            str(vdc.ComputeCapacity.Memory.Limit),
            'reserved':
            str(vdc.ComputeCapacity.Memory.Reserved),
            'used':
            humanfriendly.format_size(
                int(str(vdc.ComputeCapacity.Memory.Used)) *
                humanfriendly.parse_size(
                    '1 %s' % str(vdc.ComputeCapacity.Memory.Units)))
        }
        if hasattr(vdc.ComputeCapacity.Memory, 'Overhead'):
            result['mem_capacity'] = str(vdc.ComputeCapacity.Memory.Overhead)
    if hasattr(vdc, 'AllocationModel'):
        result['allocation_model'] = str(vdc.AllocationModel)
    if hasattr(vdc, 'VmQuota'):
        result['vm_quota'] = int(vdc.VmQuota)
    if hasattr(vdc, 'Capabilities') and \
            hasattr(vdc.Capabilities, 'SupportedHardwareVersions') and \
            hasattr(vdc.Capabilities.SupportedHardwareVersions,
                    'SupportedHardwareVersion'):
        result['supported_hw'] = []
        for n in vdc.Capabilities.SupportedHardwareVersions. \
                SupportedHardwareVersion:
            result['supported_hw'].append(str(n))
    if hasattr(vdc, 'ResourceEntities') and \
            hasattr(vdc.ResourceEntities, 'ResourceEntity'):
        result['vapps'] = []
        result['vapp_templates'] = []
        for n in vdc.ResourceEntities.ResourceEntity:
            if n.get('type') == EntityType.VAPP.value:
                result['vapps'].append(n.get('name'))
            elif n.get('type') == EntityType.VAPP_TEMPLATE.value:
                result['vapp_templates'].append(n.get('name'))
    if hasattr(vdc, 'VdcStorageProfiles') and \
            hasattr(vdc.VdcStorageProfiles, 'VdcStorageProfile'):
        result['storage_profiles'] = []
        for sp in vdc.VdcStorageProfiles.VdcStorageProfile:
            result['storage_profiles'].append(sp.get('name'))
    if access_control_settings is not None:
        result.update(access_control_settings)
    return result


def pvdc_to_dict(pvdc, refs=None, metadata=None):
    """Converts a Provider Virtual Datacenter resource to a python dictionary.

    :param lxml.objectify.ObjectifiedElement pvdc: an object containing
        EntityType.PROVIDER_VDC XML data.
    :param lxml.objectify.ObjectifiedElement refs: an object containing
        EntityType.VDC_REFERENCES XML data.
    :param lxml.objectify.ObjectifiedElement metadata: an object containing
        EntityType.METADATA XML data.

    :return: dictionary representation of pvdc object.

    :rtype: dict
    """
    result = {}
    result['name'] = pvdc.get('name')
    result['id'] = extract_id(pvdc.get('id'))
    result['description'] = str(pvdc.Description)
    if hasattr(pvdc, 'IsEnabled'):
        result['is_enabled'] = bool(pvdc.IsEnabled)
    if hasattr(pvdc, 'AvailableNetworks') and \
            hasattr(pvdc.AvailableNetworks, 'Network'):
        result['networks'] = []
        for n in pvdc.AvailableNetworks.Network:
            result['networks'].append(n.get('name'))

    if hasattr(pvdc, 'ComputeCapacity'):
        result['cpu_capacity'] = {
            'units': str(pvdc.ComputeCapacity.Cpu.Units),
            'total': str(pvdc.ComputeCapacity.Cpu.Total)
        }
        # process optional elements
        if hasattr(pvdc.ComputeCapacity.Cpu, 'Allocation'):
            result['cpu_capacity']['allocation'] = \
                str(pvdc.ComputeCapacity.Cpu.Allocation)
        if hasattr(pvdc.ComputeCapacity.Cpu, 'Reserved'):
            result['cpu_capacity']['reserved'] = \
                str(pvdc.ComputeCapacity.Cpu.Reserved)
        if hasattr(pvdc.ComputeCapacity.Cpu, 'Used'):
            result['cpu_capacity']['used'] = \
                str(pvdc.ComputeCapacity.Cpu.Used)
        if hasattr(pvdc.ComputeCapacity.Cpu, 'Overhead'):
            result['cpu_capacity']['overhead'] = \
                str(pvdc.ComputeCapacity.Cpu.Overhead)

        result['mem_capacity'] = {
            'units': str(pvdc.ComputeCapacity.Memory.Units),
            'total': str(pvdc.ComputeCapacity.Memory.Total)
        }
        # process optional elements
        if hasattr(pvdc.ComputeCapacity.Memory, 'Allocation'):
            result['mem_capacity']['allocation'] = \
                str(pvdc.ComputeCapacity.Memory.Allocation)
        if hasattr(pvdc.ComputeCapacity.Memory, 'Reserved'):
            result['mem_capacity']['reserved'] = \
                str(pvdc.ComputeCapacity.Memory.Reserved)
        if hasattr(pvdc.ComputeCapacity.Memory, 'Used'):
            result['mem_capacity']['used'] = \
                str(pvdc.ComputeCapacity.Memory.Used)
        if hasattr(pvdc.ComputeCapacity.Memory, 'Overhead'):
            result['mem_capacity']['overhead'] = \
                str(pvdc.ComputeCapacity.Memory.Overhead)

    if hasattr(pvdc, 'Capabilities') and \
            hasattr(pvdc.Capabilities, 'SupportedHardwareVersions') and \
            hasattr(pvdc.Capabilities.SupportedHardwareVersions,
                    'SupportedHardwareVersion'):
        result['supported_hw'] = []
        for n in pvdc.Capabilities.SupportedHardwareVersions. \
                SupportedHardwareVersion:
            result['supported_hw'].append(str(n))

    if hasattr(pvdc, 'Owner'):
        result['owner'] = str(pvdc.Owner)

    if hasattr(pvdc, 'StorageProfiles') and \
            hasattr(pvdc.StorageProfiles, 'ProviderVdcStorageProfile'):
        result['storage_profiles'] = []
        for sp in pvdc.StorageProfiles.ProviderVdcStorageProfile:
            result['storage_profiles'].append(sp.get('name'))

    if hasattr(pvdc, 'NetworkPoolReferences') and \
            hasattr(pvdc.NetworkPoolReferences, 'NetworkPoolReference'):
        result['network_pools'] = []
        for np in pvdc.NetworkPoolReferences.NetworkPoolReference:
            result['network_pools'].append(np.get('name'))

    if metadata is not None and hasattr(metadata, 'MetadataEntry'):
        for me in metadata.MetadataEntry:
            result['metadata: %s' % me.Key.text] = me.TypedValue.Value.text

    if hasattr(pvdc, 'Vdcs') and \
            hasattr(pvdc.Vdcs, 'Vdc'):
        result['vdc_refs'] = []
        for ref in pvdc.VdcReference:
            result['vdc_refs'].append(ref.get('name'))
    elif refs is not None and hasattr(refs, 'VdcReference'):
        result['vdc_refs'] = []
        for ref in refs.VdcReference:
            result['vdc_refs'].append(ref.get('name'))
    return result


def to_human(seconds):
    """Converts seconds to human readable (weeks, days, hours) form.

    :param int seconds: number of seconds.

    :return: (weeks, days, hours) equivalent to the seconds.

    :rtype: str
    """
    weeks = seconds / (7 * 24 * 60 * 60)
    days = seconds / (24 * 60 * 60) - 7 * weeks
    hours = seconds / (60 * 60) - 7 * 24 * weeks - 24 * days
    return '%sw, %sd, %sh' % (weeks, days, hours)


def vapp_to_dict(vapp, metadata=None, access_control_settings=None):
    """Converts a lxml.objectify.ObjectifiedElement vApp object to a dict.

    :param lxml.objectify.ObjectifiedElement vapp: an object containing
        EntityType.VAPP XML data.
    :param lxml.objectify.ObjectifiedElement access_control_settings: an object
        containing EntityType.CONTROL_ACCESS_PARAMS XML data.

    :return: dictionary representation of vApp object.

    :rtype: dict
    """
    result = {}
    result['name'] = vapp.get('name')
    if hasattr(vapp, 'Description'):
        result['description'] = str('%s' % vapp.Description)
    result['id'] = extract_id(vapp.get('id'))
    if 'ownerName' in vapp:
        result['owner'] = [vapp.get('ownerName')]
    if hasattr(vapp, 'Owner') and hasattr(vapp.Owner, 'User'):
        result['owner'] = []
        for user in vapp.Owner.User:
            result['owner'].append(user.get('name'))
    items = vapp.xpath('//ovf:NetworkSection/ovf:Network', namespaces=NSMAP)
    n = 0
    for item in items:
        n += 1
        network_name = item.get('{' + NSMAP['ovf'] + '}name')
        result['vapp-net-%s' % n] = network_name
        if hasattr(vapp, 'NetworkConfigSection'):
            for nc in vapp.NetworkConfigSection.NetworkConfig:
                if nc.get('networkName') == network_name:
                    result['vapp-net-%s-mode' % n] = \
                        nc.Configuration.FenceMode.text
    if hasattr(vapp, 'LeaseSettingsSection'):
        if hasattr(vapp.LeaseSettingsSection, 'DeploymentLeaseInSeconds'):
            result['deployment_lease'] = to_human(
                int(vapp.LeaseSettingsSection.DeploymentLeaseInSeconds))
        if hasattr(vapp.LeaseSettingsSection, 'StorageLeaseInSeconds'):
            result['storage_lease'] = to_human(
                int(vapp.LeaseSettingsSection.StorageLeaseInSeconds))
        if hasattr(vapp.LeaseSettingsSection, 'DeploymentLeaseExpiration'):
            result['deployment_lease_expiration'] = \
                vapp.LeaseSettingsSection.DeploymentLeaseExpiration
    if hasattr(vapp, 'Children') and hasattr(vapp.Children, 'Vm'):
        n = 0
        for vm in vapp.Children.Vm:
            n += 1
            k = 'vm-%s' % n
            result[k + ': name'] = vm.get('name')
            items = vm.xpath(
                'ovf:VirtualHardwareSection/ovf:Item', namespaces=NSMAP)
            for item in items:
                element_name = item.find('rasd:ElementName', NSMAP)
                connection = item.find('rasd:Connection', NSMAP)
                if connection is None:
                    quantity = item.find('rasd:VirtualQuantity', NSMAP)
                    if quantity is None or isinstance(quantity, NoneElement):
                        value = item.find('rasd:Description', NSMAP)
                    else:
                        units = item.find('rasd:VirtualQuantityUnits', NSMAP)
                        if isinstance(units, NoneElement):
                            units = ''
                        value = '{:,} {}'.format(int(quantity), units).strip()
                else:
                    value = '{}: {}'.format(
                        connection.get('{' + NSMAP['vcloud'] +
                                       '}ipAddressingMode'),
                        connection.get('{' + NSMAP['vcloud'] + '}ipAddress'))
                result['%s: %s' % (k, element_name)] = value
            env = vm.xpath('ovfenv:Environment', namespaces=NSMAP)
            if len(env) > 0:
                result['%s: %s' % (k, 'moid')] = env[0].get('{' + NSMAP['ve'] +
                                                            '}vCenterId')
            if hasattr(vm, 'StorageProfile'):
                result['%s: %s' % (k, 'storage-profile')] = \
                    vm.StorageProfile.get('name')
            if hasattr(vm, 'GuestCustomizationSection'):
                if hasattr(vm.GuestCustomizationSection, 'AdminPassword'):
                    element_name = 'password'
                    value = vm.GuestCustomizationSection.AdminPassword
                    result['%s: %s' % (k, element_name)] = value
                if hasattr(vm.GuestCustomizationSection, 'ComputerName'):
                    element_name = 'computer-name'
                    value = vm.GuestCustomizationSection.ComputerName
                    result['%s: %s' % (k, element_name)] = value
            if hasattr(vm, 'NetworkConnectionSection'):
                ncs = vm.NetworkConnectionSection
                if 'PrimaryNetworkConnectionIndex' in ncs:
                    result['%s: %s' % (k, 'primary-net')] = \
                        ncs.PrimaryNetworkConnectionIndex.text
                if 'NetworkConnection' in ncs:
                    for nc in ncs.NetworkConnection:
                        nci = nc.NetworkConnectionIndex.text
                        result['%s: net-%s' % (k, nci)] = nc.get('network')
                        result['%s: net-%s-mode' % (k, nci)] = \
                            nc.IpAddressAllocationMode.text
                        result['%s: net-%s-connected' % (k, nci)] = \
                            nc.IsConnected.text
                        if hasattr(nc, 'MACAddress'):
                            result['%s: net-%s-mac' % (k, nci)] = \
                                nc.MACAddress.text
                        if hasattr(nc, 'IpAddress'):
                            result['%s: net-%s-ip' % (k,
                                                      nci)] = nc.IpAddress.text
            if 'VmSpecSection' in vm:
                for setting in vm.VmSpecSection.DiskSection.DiskSettings:
                    if hasattr(setting, 'Disk'):
                        result['%s: attached-disk-%s-name' %
                               (k, setting.DiskId.text)] = \
                            '%s' % (setting.Disk.get('name'))
                        result['%s: attached-disk-%s-size-Mb' %
                               (k, setting.DiskId.text)] = \
                            '%s' % (setting.SizeMb.text)
                        result['%s: attached-disk-%s-bus' %
                               (k, setting.DiskId.text)] = \
                            '%s' % (setting.BusNumber.text)
                        result['%s: attached-disk-%s-unit' %
                               (k, setting.DiskId.text)] = \
                            '%s' % (setting.UnitNumber.text)

    result['status'] = VCLOUD_STATUS_MAP.get(int(vapp.get('status')))
    if access_control_settings is not None:
        result.update(access_control_settings)
    if metadata is not None and hasattr(metadata, 'MetadataEntry'):
        for me in metadata.MetadataEntry:
            result['metadata: %s' % me.Key.text] = me.TypedValue.Value.text
    return result


def task_to_dict(task):
    """Converts a lxml.objectify.ObjectifiedElement task object to a dict.

    :param lxml.objectify.ObjectifiedElement task: an object containing
        EntityType.TASK XML data.

    :return: dictionary representation of task object.

    :rtype: dict
    """
    result = to_dict(task)
    if hasattr(task, 'Owner'):
        result['owner_name'] = task.Owner.get('name')
        result['owner_href'] = task.Owner.get('href')
        result['owner_type'] = task.Owner.get('type')
    if hasattr(task, 'User'):
        result['user'] = task.User.get('name')
    if hasattr(task, 'Organization'):
        result['organization'] = task.Organization.get('name')
    if hasattr(task, 'Details'):
        result['details'] = task.Details
    return result


def disk_to_dict(disk):
    """Converts a lxml.objectify.ObjectifiedElement disk object to a dict.

    :param lxml.objectify.ObjectifiedElement disk: an object containing
        EntityType.DISK XML data.

    :return: dictionary representation of disk object.

    :rtype: dict
    """
    result = {}
    result['name'] = disk.get('name')
    result['id'] = extract_id(disk.get('id'))
    result['status'] = disk.get('status')
    result['size'] = humanfriendly.format_size(int(disk.get('size')))
    result['size_bytes'] = disk.get('size')
    result['busType'] = disk.get('busType')
    result['busSubType'] = disk.get('busSubType')
    result['iops'] = disk.get('iops')
    if hasattr(disk, 'Owner'):
        result['owner'] = disk.Owner.User.get('name')
    if hasattr(disk, 'Description'):
        result['description'] = disk.Description
    if hasattr(disk, 'StorageProfile'):
        result['storageProfile'] = disk.StorageProfile.get('name')
    if hasattr(disk, 'attached_vms') and \
       hasattr(disk.attached_vms, 'VmReference'):
        result['vms_attached'] = disk.attached_vms.VmReference.get('name')
        result['vms_attached_id'] = disk.attached_vms.VmReference.get(
            'href').split('/vm-')[-1]
    return result


def access_settings_to_dict(control_access_params):
    """Convert a lxml.objectify.ObjectifiedElement access settings to dict.

    :param lxml.objectify.ObjectifiedElement control_access_params: an object
        containing EntityType.CONTROL_ACCESS_PARAMS XML data.

    :return: dict representation of access control settings.

    :rtype: dict
    """
    result = {}
    if hasattr(control_access_params, 'IsSharedToEveryone'):
        result['is_shared_to_everyone'] = control_access_params[
            'IsSharedToEveryone']
    if hasattr(control_access_params, 'EveryoneAccessLevel'):
        result['everyone_access_level'] = control_access_params[
            'EveryoneAccessLevel']
    if hasattr(control_access_params, 'AccessSettings') and \
            hasattr(control_access_params.AccessSettings,
                    'AccessSetting') and \
            len(control_access_params.AccessSettings.AccessSetting) > 0:
        n = 1
        for access_setting in list(
                control_access_params.AccessSettings.AccessSetting):
            access_str = 'access_settings'
            if hasattr(access_setting, 'Subject'):
                result['%s_%s_subject_name' % (access_str, n)] = \
                    access_setting.Subject.get('name')
            if hasattr(access_setting, 'Subject'):
                result['%s_%s_subject_href' % (access_str, n)] = \
                    access_setting.Subject.get('href')
            if hasattr(access_setting, 'Subject'):
                result['%s_%s_subject_type' % (access_str, n)] = \
                    access_setting.Subject.get('type')
            if hasattr(access_setting, 'AccessLevel'):
                result['%s_%s_access_level' % (access_str, n)] = \
                    access_setting.AccessLevel
            n += 1
    return result


def metadata_to_dict(metadata):
    """Converts a lxml.objectify.ObjectifiedElement metadata object to a dict.

    All MetadataEntry tags in the metadata object is converted to simple
    key-value pair.

    :param lxml.objectify.ObjectifiedElement metadata: an object containing
        EntityType.METADATA XML data.

    :return: dictionary representation of metadata entries. All keys and values
        will be string.

    :rtype: dict
    """
    result = {}
    if hasattr(metadata, 'MetadataEntry'):
        for entry in metadata.MetadataEntry:
            key, value = metadata_entry_to_tuple(entry)
            result[key] = value
    return result


def metadata_entry_to_tuple(metadata_entry):
    """Converts a lxml.objectify.ObjectifiedElement metadata entry to a tuple.

    The metadata entry object is converted into a simple (key, value) tuple.

    :param lxml.objectify.ObjectifiedElement metadata_entry: an object
        containing MetadataEntry XML data. This tag is a child tag of
        EntityType.Metadata XML.

    :return: a key-value tuple respresnting the metadata entry. Both key and
        value will be strings.

    :rtype: tuple
    """
    key = metadata_entry.Key.text
    value = metadata_entry.TypedValue.Value.text
    return (key, value)


def extract_metadata_value(metadata_value):
    """Converts a lxml.objectify.ObjectifiedElement metadata value to a string.

    The textual representation of the metadata value is extracted out of the
    metadata value object.

    :param lxml.objectify.ObjectifiedElement metadata_value: an object
        containing EntityType.METADATA_VALUE XML data.

    :return: string representation of the metadata value

    :rtype: str
    """
    return metadata_value.TypedValue.Value.text


def filter_attributes(resource_type):
    """Returns a list of attributes for a given resource type.

    :param str resource_type: type of resource whose list of attributes we want
        to extract. Valid values are 'adminTask', 'task', 'adminVApp', 'vApp'
        and 'adminCatalogItem', 'catalogItem'.

    :return: the list of attributes that are relevant for the given resource
        type.

    :rtype: list
    """
    attributes = None
    if resource_type in ['adminTask', 'task']:
        attributes = ['id', 'name', 'objectName', 'status', 'startDate']
    elif resource_type in ['adminVApp', 'vApp']:
        attributes = [
            'id', 'name', 'numberOfVMs', 'status', 'numberOfCpus',
            'memoryAllocationMB', 'storageKB', 'ownerName', 'isDeployed',
            'isEnabled', 'vdcName'
        ]
    elif resource_type in ['adminCatalogItem', 'catalogItem']:
        attributes = [
            'id', 'name', 'catalogName', 'storageKB', 'status', 'entityType',
            'vdcName', 'isPublished', 'ownerName'
        ]
    return attributes


def to_dict(obj, attributes=None, resource_type=None, exclude=['href',
                                                               'type']):
    """Converts generic lxml.objectify.ObjectifiedElement to a dictionary.

    :param lxml.objectify.ObjectifiedElement obj:
    :param list attributes: list of attributes we want to extract from the XML
        object.
    :param str resource_type: type of resource in the param obj. Acceptable
        values are listed in the enum pyvcloud.vcd.client.ResourceType.
    :param list exclude: list of attributes that should be excluded from the
        dictionary.

    :return: the dictionary representing the object.

    :rtype: dict
    """
    if obj is None:
        return {}
    result = {}
    attributes_res = filter_attributes(resource_type)
    if attributes:
        for attr in attributes:
            result[attr] = None
    if attributes_res:
        for attr in attributes_res:
            result[attr] = None
    for attr in obj.attrib:
        flag = False
        if attributes:
            flag = attr in attributes
        elif attributes_res:
            flag = attr in attributes_res
        else:
            flag = True
        if flag:
            if attr == 'id':
                result[attr] = extract_id(obj.get(attr))
            else:
                result[attr] = obj.get(attr)
    if hasattr(obj, '__dict__'):
        for key in obj.__dict__:
            result[key] = obj[key].text
    for e in exclude:
        if e in result.keys():
            result.pop(e)
    return result


def to_camel_case(name, names):
    result = name
    for n in names:
        if name.lower() == n.lower():
            return n
    return result


def stdout_xml(the_xml, is_colorized=True):
    """Prints an lxml.objectify.ObjectifiedElement to console.

    :param lxml.objectify.ObjectifiedElement the_xml: the object we want to
        print.
    :param bool is_colorized: if True, will print highlight xml tags and
        attributes else will print b&w output to the console.
    """
    message = str(etree.tostring(the_xml, pretty_print=True), 'utf-8')
    if is_colorized:
        print(
            highlight(message, lexers.XmlLexer(),
                      formatters.TerminalFormatter()))
    else:
        print(message)


def get_admin_href(href):
    """Returns admin version of a given vCD url.

    This function is idempotent, which also means that if input href is already
    an admin href no further action would be taken.

    :param str href: the href whose admin version we need.

    :return: admin version of the href.

    :rtype: str
    """
    if '/api/admin/extension/' in href:
        return href.replace('/api/admin/extension', '/api/admin/')
    elif '/api/admin/' in href:
        return href
    else:
        return href.replace('/api/', '/api/admin/')


def get_admin_extension_href(href):
    """Returns sys admin version of a given vCD url.

    This function is idempotent, which also means that if input href is already
    an admin extension href no further action would be taken.

    :param str href: the href whose sys admin version we need.

    :return: sys admin version of the href.

    :rtype: str
    """
    if '/api/admin/extension/' in href:
        return href
    elif '/api/admin/' in href:
        return href.replace('/api/admin/', '/api/admin/extension/')
    else:
        return href.replace('/api/', '/api/admin/extension/')


def _badpath(path, base):
    """Determines if a given file path is under a given base path or not.

    :param str path: file path where the file will be extracted to.
    :param str base: path to the current working directory.

    :return: False, if the path is under the given base, else True.

    :rtype: bool
    """
    # joinpath will ignore base if path is absolute
    return not realpath(abspath(joinpath(base, path))).startswith(base)


def _badlink(info, base):
    """Determine if a given link is under a given base path or not.

    :param TarInfo info: file that is going to be extracted.
    :param str base: path to the current working directory.

    :return: False, if the path is under the given base, else True.

    :rtype: bool
    """
    # Links are interpreted relative to the directory containing the link
    tip = realpath(abspath(joinpath(base, dirname(info.name))))
    return _badpath(info.linkname, base=tip)


def get_safe_members_in_tar_file(tarfile):
    """Retrieve members of a tar file that are safe to extract.

    :param Tarfile tarfile: the archive that has been opened as a TarFile
        object.

    :return: list of members in the archive that are safe to extract.

    :rtype: list
    """
    base = realpath(abspath(('.')))
    result = []
    for finfo in tarfile.getmembers():
        if _badpath(finfo.name, base):
            print(finfo.name + ' is blocked: illegal path.')
        elif finfo.issym() and _badlink(finfo, base):
            print(finfo.name + ' is blocked: Symlink to ' + finfo.linkname)
        elif finfo.islnk() and _badlink(finfo, base):
            print(finfo.name + ' is blocked: Hard link to ' + finfo.linkname)
        else:
            result.append(finfo)
    return result


def cidr_to_netmask(cidr):
    """Convert CIDR to netmask.

    :param str cidr: CIDR in the format of 10.2.2.1/20

    :return network address and netmask

    :rtype: str, str
    """
    gateway_ip = cidr.split('/')[0]
    ipv4 = IPv4Network(cidr, False)
    return gateway_ip, ipv4.netmask


def netmask_to_cidr_prefix_len(network, netmask):
    """Determine CIDR prefix length from network and netmask.

    :param str network: gateway IP

    :param str netmask: netmask

    :return prefix len

    :rtype: int
    """
    subnet = network + '/' + netmask
    return IPv4Network(subnet, False).prefixlen


def build_network_url_from_gateway_url(gateway_href):
    """Build network URI for NSX Proxy API.

    It replaces '/api/edgeGatway/' or '/api/admin/edgeGatway/' with
    /network/EDGE_ENDPOINT and return the newly formed network URI.

    param: str gateway_href: gateway URL. for ex:
    https://x.x.x.x/api/admin/edgeGateway/uuid

    return network href
    rtype: str
    """
    _NETWORK_URL = '/network/edges/'
    _GATEWAY_API_URL = '/api/edgeGateway/'
    _GATEWAY_ADMIN_API_URL = '/api/admin/edgeGateway/'
    network_url = gateway_href
    if gateway_href.find(_GATEWAY_API_URL) > 0 or gateway_href.find(
            _GATEWAY_ADMIN_API_URL) > 0:
        network_url = network_url.replace(_GATEWAY_API_URL, _NETWORK_URL)
        return network_url.replace(_GATEWAY_ADMIN_API_URL, _NETWORK_URL)

    return None
