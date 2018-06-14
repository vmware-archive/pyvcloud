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
from pyvcloud.vcd.exceptions import InvalidParameterException
from pyvcloud.vcd.utils import get_admin_href


class PVDC(object):
    def __init__(self, client, href=None, resource=None):
        """Constructor for a PVDC object.

        :param pyvcloud.vcd.client.Client client: the client that will be used
            to make REST calls to vCD.
        :param str href: URI of the entity.
        :param lxml.objectify.ObjectifiedElement resource: object containing
            EntityType.PROVIDER_VDC XML data representing the provider vdc.
        """
        self.client = client
        if href is None and resource is None:
            raise InvalidParameterException(
                "PVDC initialization failed as arguments are either invalid "
                "or None")
        self.href = href
        self.resource = resource
        if resource is not None:
            self.name = resource.get('name')
            self.href = resource.get('href')
        self.admin_resource = get_admin_href(self.href)

    def get_resource(self):
        """Fetches the XML representation of the provider vdc from vCD.

        Will serve cached response if possible.

        :return: object containing EntityType.PROVIDER_VDC XML data
            representing the concerned provider vdc.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        return self.resource

    def reload(self):
        """Reloads the resource representation of the provider vdc.

        This method should be called in between two method invocations on the
        PVDC object, if the former call changes the representation of the
        provider vdc in vCD.
        """
        self.resource = self.client.get_resource(self.href)
        if self.resource is not None:
            self.name = self.resource.get('name')
            self.href = self.resource.get('href')

    def get_vdc_references(self):
        """List all provider vdc references.

        :return: an object containing VMWProviderVdcReference XML element that
            refers to provider vdcs.

        :rtype: lxml.objectify.StringElement
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        return self.client.get_linked_resource(
            self.resource, RelationType.DOWN, EntityType.VDC_REFERENCES.value)

    def get_metadata(self):
        """Fetch metadata of the provider vdc.

        :return: an object containing EntityType.METADATA XML data which
            represents the metadata associated with the provider vdc.

        :rtype: lxml.objectify.ObjectifiedElement
        """
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
        """Set metadata of the provider vdc.

        :param str domain:
        :param str visibility:
        :param str key:
        :param str value:
        :param str metadata_type:

        :return: an object containing EntityType.METADATA XML data which
            represents the updated metadata associated with the provider vdc.

        :rtype: lxml.objectify.ObjectifiedElement
        """
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
