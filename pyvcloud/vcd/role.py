# VMware vCloud Director Python SDK
# Copyright (c) 2017-2018 VMware, Inc. All Rights Reserved.
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

from copy import deepcopy

from pyvcloud.vcd.client import E
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.exceptions import InvalidParameterException


class Role(object):
    def __init__(self, client, href=None, resource=None):
        """Constructor for Role object.

        :param pyvcloud.vcd.client.Client client: the client that will be used
            to make REST calls to vCD.
        :param str href: URI of the Role entity
        :param lxml.objectify.ObjectifiedElement resource: object containing
            EntityType.ROLE XML data representing the role.
        """
        self.client = client
        if href is None and resource is None:
            raise InvalidParameterException(
                "Role initialization failed as arguments are either invalid "
                "or None")
        self.href = href
        self.resource = resource
        if resource is not None:
            self.href = resource.get('href')
            self.name = resource.get('name')

    def list_rights(self):
        """List rights associated with the role.

        :return: names of rights for a given role.

        :rtype: list
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
        """Unlinks the role from its template."""
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        self.client.post_linked_resource(self.resource,
                                         RelationType.UNLINK_FROM_TEMPLATE,
                                         EntityType.ROLE.value, None)

    def link(self):
        """Links the role to its template."""
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        self.client.post_linked_resource(self.resource,
                                         RelationType.LINK_TO_TEMPLATE,
                                         EntityType.ROLE.value, None)

    def add_rights(self, rights, org):
        """Adds list of rights to a given role.

        :param list rights: right names as a list of strings.
        :param pyvcloud.vcd.org.Org org: organization to which the role
            belongs.

        :return: an object containing EntityType.ROLE XML data which represents
            the updated role.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        updated_resource = deepcopy(self.resource)
        for right in rights:
            right_record = org.get_right_record(right)
            updated_resource.RightReferences.append(
                E.RightReference(
                    name=right_record.get('name'),
                    href=right_record.get('href'),
                    type=EntityType.RIGHT.value))
        return self.client.put_resource(self.href, updated_resource,
                                        EntityType.ROLE.value)

    def remove_rights(self, rights):
        """Removes list of rights from a given role.

        :param list rights: right names as a list of strings.

        :return: an object containing EntityType.ROLE XML data which represents
            the updated role.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.resource = self.client.get_resource(self.href)
        updated_resource = deepcopy(self.resource)
        if hasattr(self.resource, 'RightReferences') and \
                hasattr(self.resource.RightReferences, 'RightReference'):
            right_references = updated_resource.RightReferences.RightReference
            for right_reference in list(right_references):
                for right in rights:
                    if right_reference.get('name') == right:
                        updated_resource.RightReferences\
                            .remove(right_reference)
                        break
        return self.client.put_resource(self.href, updated_resource,
                                        EntityType.ROLE.value)
