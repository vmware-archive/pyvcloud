# VMware vCloud Director Python SDK
# Copyright (c) 2018 VMware, Inc. All Rights Reserved.
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
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.utils import get_admin_href


class PVDC(object):
    def __init__(self, client, href=None, resource=None):
        """Constructor for a PVDC object.

        :param client:  (pyvcloud.vcd.client): The client.
        :param href: (str): URI of the entity.
        :param resource: (lxml.objectify.ObjectifiedElement): XML
            representation of the entity.
        """
        self.client = client
        if href is None and resource is None:
            raise TypeError("PVDC initialization failed as arguments"
                            " are either invalid or None")
        self.href = href
        self.resource = resource
        if resource is not None:
            self.name = resource.get('name')
            self.href = resource.get('href')
        self.admin_resource = get_admin_href(self.href)

    def get_resource(self):
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        return self.resource

    def reload(self):
        self.resource = self.client.get_resource(self.href)
        if self.resource is not None:
            self.name = self.resource.get('name')
            self.href = self.resource.get('href')

    def get_vdc_references(self):
        """List provider VDC references backed by the Provider VDC.

        :return: (VdcReferences)  A :class:`lxml.objectify.StringElement`
                                  object describing the VDC References.
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        return self.client.get_linked_resource(
            self.resource, RelationType.DOWN, EntityType.VDC_REFERENCES.value)

    def get_metadata(self):
        if self.resource is None:
            self.resource = self.client.get_resource(self.admin_href)
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
