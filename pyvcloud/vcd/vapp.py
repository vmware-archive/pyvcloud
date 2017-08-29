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
from lxml import objectify
from pyvcloud.vcd.client import E
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import RelationType


class VApp(object):

    def __init__(self, client, name=None, vapp_href=None, vapp_resource=None):
        self.client = client
        self.name = name
        self.href = vapp_href
        self.vapp_resource = vapp_resource
        if vapp_resource is not None:
            self.name = vapp_resource.get('name')
            self.href = vapp_resource.get('href')

    def get_primary_ip(self, vm_name):
        if self.vapp_resource is None:
            self.vapp_resource = self.client.get_resource(self.href)
        if hasattr(self.vapp_resource, 'Children') and \
           hasattr(self.vapp_resource.Children, 'Vm'):
            for vm in self.vapp_resource.Children.Vm:
                if vm_name == vm.get('name'):
                    items = vm.xpath(
                        '//ovf:VirtualHardwareSection/ovf:Item',
                        namespaces=NSMAP)
                    for item in items:
                        connection = item.find('rasd:Connection', NSMAP)
                        if connection is not None:
                            return connection.get('{http://www.vmware.com/vcloud/v1.5}ipAddress')  # NOQA
        raise Exception('can\'t find ip address')

    def set_metadata(self,
                     domain,
                     visibility,
                     key,
                     value,
                     metadata_type='MetadataStringValue'):
        if self.vapp_resource is None:
            self.vapp_resource = self.client.get_resource(self.href)
        new_metadata = E.Metadata(
            E.MetadataEntry(
                {'type': 'xs:string'},
                E.Domain(domain, visibility=visibility),
                E.Key(key),
                E.TypedValue(
                    {'{http://www.w3.org/2001/XMLSchema-instance}type':
                     'MetadataStringValue'},
                    E.Value(value))))
        metadata = self.client.get_linked_resource(self.vapp_resource,
                                                   RelationType.DOWN,
                                                   EntityType.METADATA.value)
        return self.client.post_linked_resource(metadata,
                                                RelationType.ADD,
                                                EntityType.METADATA.value,
                                                new_metadata)

    def get_vm_moid(self, vm_name):
        if self.vapp_resource is None:
            self.vapp_resource = self.client.get_resource(self.href)
        vapp = self.vapp_resource
        if hasattr(vapp, 'Children') and hasattr(vapp.Children, 'Vm'):
            for vm in vapp.Children.Vm:
                if vm.get('name') == vm_name:
                    env = vm.xpath('//ovfenv:Environment', namespaces=NSMAP)
                    if len(env) > 0:
                        return env[0].get('{http://www.vmware.com/schema/ovfenv}vCenterId')  # NOQA
        return None

    def set_lease(self, deployment_lease=0, storage_lease=0):
        if self.vapp_resource is None:
            self.vapp_resource = self.client.get_resource(self.href)
        new_section = self.vapp_resource.LeaseSettingsSection

        new_section.DeploymentLeaseInSeconds = deployment_lease
        new_section.StorageLeaseInSeconds = storage_lease
        objectify.deannotate(new_section)
        etree.cleanup_namespaces(new_section)
        return self.client.put_resource(
            self.vapp_resource.get('href') + '/leaseSettingsSection/',
            new_section,
            EntityType.LEASE_SETTINGS.value)
