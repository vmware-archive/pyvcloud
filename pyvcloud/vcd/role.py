# VMware vCloud Director Python SDK
# Copyright (c) 2017 VMware, Inc. All Rights Reserved.
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

from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import RelationType


class Role(object):
    def __init__(self, client, href=None, resource=None):
        """Constructor for Role object

        :param client: (pyvcloud.vcd.client): The client.
        :param href: URI of the Role entity
        :param resource: (lxml.objectify.ObjectifiedElement): XML
            representation of the entity.
        """
        self.client = client
        self.href = href
        self.resource = resource
        if resource is not None:
            self.href = resource.get('href')
            self.name = resource.get('name')

    def list_rights(self):
        """List rights associated with the role

        :return: list of names of rights for a given role.
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        rights = []
        if hasattr(self.resource, 'RightReferences') and \
                hasattr(self.resource.RightReferences, 'RightReference'):
            for right in self.resource.RightReferences.RightReference:
                rights.append({'name': right.get('name')})
        return rights

    def unlink(self):
        """Unlinks the role from its template.

        :return: None
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        self.client.post_linked_resource(
            self.resource, RelationType.UNLINK_FROM_TEMPLATE,
            EntityType.ROLE.value, None)

    def link(self):
        """Links the role to its template.

        :return: None
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        self.client.post_linked_resource(
            self.resource, RelationType.LINK_TO_TEMPLATE,
            EntityType.ROLE.value, None)
