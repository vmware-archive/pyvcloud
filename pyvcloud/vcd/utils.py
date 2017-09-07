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

from lxml.objectify import NoneElement
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
    result['vdcs'] = [str(n.name) for n in
                      get_links(org, media_type=EntityType.VDC.value)]
    result['org_networks'] = [str(n.name) for n in
                              get_links(org, media_type=EntityType.
                                        ORG_NETWORK.value)]
    result['catalogs'] = [str(n.name) for n in
                          get_links(org, media_type=EntityType.CATALOG.value)]
    return result


def vdc_to_dict(vdc):
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
    if hasattr(vdc, 'AllocationModel'):
        result['allocation_model'] = str(vdc.AllocationModel)
    if hasattr(vdc, 'VmQuota'):
        result['vm_quota'] = int(vdc.VmQuota)
    if hasattr(vdc, 'Capabilities') and \
       hasattr(vdc.Capabilities, 'SupportedHardwareVersions') and \
       hasattr(vdc.Capabilities.SupportedHardwareVersions,
               'SupportedHardwareVersion'):
        result['supported_hw'] = []
        for n in vdc.Capabilities.SupportedHardwareVersions.\
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
    return result


def to_human(seconds):
    weeks = seconds / (7*24*60*60)
    days = seconds / (24*60*60) - 7*weeks
    hours = seconds / (60*60) - 7*24*weeks - 24*days
    return '%sw, %sd, %sh' % (weeks, days, hours)


def vapp_to_dict(vapp):
    result = {}
    result['name'] = vapp.get('name')
    result['id'] = extract_id(vapp.get('id'))
    if 'ownerName' in vapp:
        result['owner'] = [vapp.get('ownerName')]
    if hasattr(vapp, 'Owner') and hasattr(vapp.Owner, 'User'):
        result['owner'] = []
        for user in vapp.Owner.User:
            result['owner'].append(user.get('name'))
    if hasattr(vapp, 'LeaseSettingsSection'):
        if hasattr(vapp.LeaseSettingsSection, 'DeploymentLeaseInSeconds'):
            result['deployment_lease'] = to_human(int(vapp.
                                                      LeaseSettingsSection.
                                                      DeploymentLeaseInSeconds
                                                      )
                                                  )
        if hasattr(vapp.LeaseSettingsSection, 'StorageLeaseInSeconds'):
            result['storage_lease'] = to_human(int(vapp.
                                                   LeaseSettingsSection.
                                                   StorageLeaseInSeconds))
        if hasattr(vapp.LeaseSettingsSection, 'DeploymentLeaseExpiration'):
            result['deployment_lease_expiration'] = \
                vapp.LeaseSettingsSection.DeploymentLeaseExpiration
    if hasattr(vapp, 'Children') and hasattr(vapp.Children, 'Vm'):
        n = 0
        for vm in vapp.Children.Vm:
            n += 1
            k = 'vm-%s' % n
            result[k] = vm.get('name')
            items = vm.xpath(
                '//ovf:VirtualHardwareSection/ovf:Item',
                namespaces=NSMAP)
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
                                        connection.get('{http://www.vmware.com/vcloud/v1.5}ipAddressingMode'),  # NOQA
                                        connection.get('{http://www.vmware.com/vcloud/v1.5}ipAddress'))  # NOQA
                result['%s: %s' % (k, element_name)] = value
            env = vm.xpath('//ovfenv:Environment', namespaces=NSMAP)
            if len(env) > 0:
                result['%s: %s' % (k, 'moid')] = env[0].get('{http://www.vmware.com/schema/ovfenv}vCenterId')  # NOQA
            if hasattr(vm.GuestCustomizationSection, 'AdminPassword'):
                element_name = 'password'
                value = vm.GuestCustomizationSection.AdminPassword
                result['%s: %s' % (k, element_name)] = value
            if hasattr(vm.GuestCustomizationSection, 'ComputerName'):
                element_name = 'computer-name'
                value = vm.GuestCustomizationSection.ComputerName
                result['%s: %s' % (k, element_name)] = value
    result['status'] = VCLOUD_STATUS_MAP.get(int(vapp.get('status')))
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


def filter_attributes(resource_type):
    attributes = None
    if resource_type in ['adminTask', 'task']:
        attributes = ['id', 'name', 'objectName', 'status',
                      'startDate']
    elif resource_type in ['adminVApp', 'vApp']:
        attributes = ['id', 'name', 'numberOfVMs', 'status', 'numberOfCpus',
                      'memoryAllocationMB', 'storageKB', 'ownerName',
                      'isDeployed', 'isEnabled']
    elif resource_type in ['adminCatalogItem', 'catalogItem']:
        attributes = ['id', 'name', 'catalogName', 'storageKB', 'status',
                      'entityType', 'vdcName', 'isPublished', 'ownerName']
    return attributes


def to_dict(obj,
            attributes=None,
            resource_type=None,
            exclude=['href', 'type']):
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
