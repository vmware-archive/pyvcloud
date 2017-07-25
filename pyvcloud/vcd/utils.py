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

from pyvcloud.vcd.client import QueryResultFormat
from pyvcloud.vcd.client import get_links
from pyvcloud.vcd.client import EntityType


def to_dict(obj, attributes):
    result = {}
    for attr in attributes:
        if attr in obj.attrib:
            result[attr] = obj.get(attr)
    return result


def org_to_dict(org):
    result = {}
    result['name'] = org.get('name')
    result['id'] =  org.get('id')
    result['full_name'] = str('%s' % org.FullName)
    result['description'] = str('%s' % org.Description)
    result['vdcs'] = [str(n.name) for n in
        get_links(org, media_type=EntityType.VDC.value)]
    result['org_networks'] = [str(n.name) for n in
        get_links(org, media_type=EntityType.ORG_NETWORK.value)]
    result['catalogs'] = [str(n.name) for n in
        get_links(org, media_type=EntityType.CATALOG.value)]
    return result


def vdc_to_dict(vdc):
    result = {}
    result['name'] = vdc.get('name')
    result['id'] = vdc.get('id')
    result['is_enabled'] = bool(vdc.IsEnabled)
    result['networks'] = []
    if hasattr(vdc, 'AvailableNetworks') and \
       hasattr(vdc.AvailableNetworks, 'Network'):
        for n in vdc.AvailableNetworks.Network:
            result['networks'].append(n.get('name'))
    result['cpu_capacity'] = {
        'units': str(vdc.ComputeCapacity.Cpu.Units),
        'allocated': str(vdc.ComputeCapacity.Cpu.Allocated),
        'limit': str(vdc.ComputeCapacity.Cpu.Limit),
        'reserved': str(vdc.ComputeCapacity.Cpu.Reserved),
        'used': str(vdc.ComputeCapacity.Cpu.Used),
        'overhead': str(vdc.ComputeCapacity.Cpu.Overhead)
    }
    result['mem_capacity'] = {
        'units': str(vdc.ComputeCapacity.Memory.Units),
        'allocated': str(vdc.ComputeCapacity.Memory.Allocated),
        'limit': str(vdc.ComputeCapacity.Memory.Limit),
        'reserved': str(vdc.ComputeCapacity.Memory.Reserved),
        'used': str(vdc.ComputeCapacity.Memory.Used),
        'overhead': str(vdc.ComputeCapacity.Memory.Overhead)
    }
    result['allocation_model'] = str(vdc.AllocationModel)
    result['vm_quota'] = int(vdc.VmQuota)
    result['supported_hw'] = []
    if hasattr(vdc, 'Capabilities') and \
       hasattr(vdc.Capabilities, 'SupportedHardwareVersions') and \
       hasattr(vdc.Capabilities.SupportedHardwareVersions, \
               'SupportedHardwareVersion'):
        for n in vdc.Capabilities.SupportedHardwareVersions. \
                 SupportedHardwareVersion:
            result['supported_hw'].append(str(n))
    result['vapps'] = []
    result['vapp_templates'] = []
    if hasattr(vdc, 'ResourceEntities') and \
       hasattr(vdc.ResourceEntities, 'ResourceEntity'):
        for n in vdc.ResourceEntities.ResourceEntity:
            if n.get('type') == EntityType.VAPP.value:
                result['vapps'].append(n.get('name'))
            elif n.get('type') == EntityType.VAPP_TEMPLATE.value:
                result['vapp_templates'].append(n.get('name'))
    return result


def vapp_to_dict(vapp):
    result = {}
    result['name'] = vapp.get('name')
    result['id'] =  vapp.get('id')
    result['owner'] = []
    if hasattr(vapp, 'Owner') and hasattr(vapp.Owner, 'User'):
        for user in vapp.Owner.User:
            result['owner'].append(user.get('name'))
    result['vms'] = []
    if hasattr(vapp, 'Children') and hasattr(vapp.Children, 'Vm'):
        for user in vapp.Children.Vm:
            result['vms'].append(user.get('name'))
    return result
