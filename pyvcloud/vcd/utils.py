# VMware vCloud Python SDK
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
    if urn is None:
        return None
    if ':' in urn:
        return urn.split(':')[-1]
    else:
        return urn


def org_to_dict(org):
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
                int(str(vdc.ComputeCapacity.Memory.Used)) * humanfriendly.
                parse_size('1 %s' % str(vdc.ComputeCapacity.Memory.Units)))
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

    :param pvdc: (ProviderVdcType): xml object
    :param refs: (VdcReferences): xml object retrieved from
           the ProviderVdcType.
    :param metadata: (Metadata): xml object metadata retrieved from
           the ProviderVdcType.
    :return: (dict): dict representation of pvdc object.
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
    weeks = seconds / (7 * 24 * 60 * 60)
    days = seconds / (24 * 60 * 60) - 7 * weeks
    hours = seconds / (60 * 60) - 7 * 24 * weeks - 24 * days
    return '%sw, %sd, %sh' % (weeks, days, hours)


def vapp_to_dict(vapp, metadata=None, access_control_settings=None):
    result = {}
    result['name'] = vapp.get('name')
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
                        connection.get(
                            '{' + NSMAP['vcloud'] + '}ipAddressingMode'),
                        connection.get('{' + NSMAP['vcloud'] + '}ipAddress'))
                result['%s: %s' % (k, element_name)] = value
            env = vm.xpath('ovfenv:Environment', namespaces=NSMAP)
            if len(env) > 0:
                result['%s: %s' %
                       (k,
                        'moid')] = env[0].get('{' + NSMAP['ve'] + '}vCenterId')
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
    """Convert access settings to dict.

    :param control_access_params: (ControlAccessParamsType): xml object
    representing access settings.
    :return: (dict): dict representation of access control settings.
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


def filter_attributes(resource_type):
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
    message = str(etree.tostring(the_xml, pretty_print=True), 'utf-8')
    if is_colorized:
        print(
            highlight(message, lexers.XmlLexer(),
                      formatters.TerminalFormatter()))
    else:
        print(message)


def get_admin_href(href):
    return href.replace('/api/', '/api/admin/')


def get_admin_extension_href(href):
    if '/api/admin/' in href:
        return href.replace('/api/admin/', '/api/admin/extension/')
    else:
        return href.replace('/api/', '/api/admin/extension/')
