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

from pyvcloud.vcd.client import E
from pyvcloud.vcd.client import EntityType
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

    def get_primary_ip(self, timeout=300):
        pass

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
