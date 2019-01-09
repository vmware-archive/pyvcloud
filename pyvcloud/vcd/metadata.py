# VMware vCloud Director Python SDK
# Copyright (c) 2014-2019 VMware, Inc. All Rights Reserved.
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
from pyvcloud.vcd.client import MetadataDomain
from pyvcloud.vcd.client import MetadataValueType
from pyvcloud.vcd.client import MetadataVisibility
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.exceptions import InvalidParameterException
from pyvcloud.vcd.utils import get_admin_href


class Metadata(object):
    def __init__(self, client, href=None, resource=None):
        """Constructor for metadata object.

        :param pyvcloud.vcd.client.Client client: the client that will be used
            to make REST calls to vCD.
        :param str href: non admin URI of the metadata. With the exception of
            provider VDC related metadata objects, those will be initiated with
            admin href (since non admin href of pVDC doesn't exist).
        :param lxml.objectify.ObjectifiedElement resource: object containing
            EntityType.METADATA XML data representing metadata of a vCD object.
        """
        self.client = client
        if href is None and resource is None:
            raise InvalidParameterException(
                "Metadata initialization failed as arguments are either "
                "invalid or None")
        self.href = href
        self.resource = resource
        if resource is not None:
            self.href = resource.get('href')

    def get_resource(self):
        """Fetches the XML representation of the metadata from vCD.

        Will serve cached response if possible.

        :return: object containing EntityType.METADATA XML data representing
            the metadata.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.reload()
        return self.resource

    def reload(self):
        """Reloads the resource representation of the metadata.

        This method should be called in between two method invocations on the
        metadata object or it's parent, if the former call changes the
        representation of the metadata in vCD.
        """
        self.resource = self.client.get_resource(self.href)

    def get_all_metadata(self, use_admin_endpoint=False):
        """Fetch all metadata entries of the parent object.

        :param bool use_admin_endpoint: if True, will use the /api/admin
            endpoint to retrieve the metadata object else will use the vanilla
            /api endpoint.

        :return: an object containing EntityType.METADATA XML data which
            represents the metadata entries associated with parent object.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if not use_admin_endpoint:
            return self.get_resource()
        else:
            admin_href = get_admin_href(self.href)
            return self.client.get_resource(admin_href)

    def set_metadata(self,
                     key,
                     value,
                     domain=MetadataDomain.GENERAL,
                     visibility=MetadataVisibility.READ_WRITE,
                     metadata_value_type=MetadataValueType.STRING,
                     use_admin_endpoint=False):
        """Add/update a metadata entry to/of the parent object.

        If an entry with the same key exists, it will be updated with the new
        value.

        :param str key: an arbitrary key name. Length cannot exceed 256 UTF-8
            characters.
        :param str value: value of the metadata entry
        :param client.MetadataDomain domain: domain where the new entry would
            be put.
        :param client.MetadataVisibility visibility: visibility of the metadata
            entry.
        :param client.MetadataValueType metadata_value_type:
        :param bool use_admin_endpoint: if True, will use the /api/admin
            endpoint to add new entry to the metadata object else will use the
            vanilla /api endpoint.

        :return: an object of type EntityType.TASK XML which represents
            the asynchronous task that is updating the metadata.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        key_value_dict = {key: value}
        return self.set_multiple_metadata(
            key_value_dict=key_value_dict,
            domain=domain,
            visibility=visibility,
            metadata_value_type=metadata_value_type,
            use_admin_endpoint=use_admin_endpoint)

    def set_multiple_metadata(self,
                              key_value_dict,
                              domain=MetadataDomain.GENERAL,
                              visibility=MetadataVisibility.READ_WRITE,
                              metadata_value_type=MetadataValueType.STRING,
                              use_admin_endpoint=False):
        """Add/update multiple metadata entries to/of the parent object.

        If an entry with the same key exists, it will be updated with the new
        value. All entries must have the same value type and will be written to
        the same domain with identical visibility.

        :param dict key_value_dict: a dict containing key-value pairs to be
            added/updated.
        :param client.MetadataDomain domain: domain where the new entries would
            be put.
        :param client.MetadataVisibility visibility: visibility of the metadata
            entries.
        :param client.MetadataValueType metadata_value_type:
        :param bool use_admin_endpoint: if True, will use the /api/admin
            endpoint to add new entries to the metadata object else will use
            the vanilla /api endpoint.

        :return: an object of type EntityType.TASK XML which represents
            the asynchronous task that is updating the metadata entries.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if not isinstance(domain, MetadataDomain):
            raise InvalidParameterException('Invalid domain.')
        if not isinstance(visibility, MetadataVisibility):
            raise InvalidParameterException('Invalid visibility.')
        if not isinstance(metadata_value_type, MetadataValueType):
            raise InvalidParameterException('Invalid type of value.')

        metadata = self.get_all_metadata(use_admin_endpoint)
        new_metadata = E.Metadata()
        for k, v in key_value_dict.items():
            entry = E.MetadataEntry(
                {'type': 'xs:string'},
                E.Domain(domain.value, visibility=visibility.value),
                E.Key(k),
                E.TypedValue(
                    {'{' + NSMAP['xsi'] + '}type': metadata_value_type.value},
                    E.Value(v)))
            new_metadata.append(entry)
        return self.client.post_linked_resource(metadata, RelationType.ADD,
                                                EntityType.METADATA.value,
                                                new_metadata)

    def get_metadata_value(self,
                           key,
                           domain=MetadataDomain.GENERAL,
                           use_admin_endpoint=False):
        """Fetch a metadata value identified by the domain and key.

        :param str key: key of the value to be fetched.
        :param client.MetadataDomain domain: domain of the value to be fetched.
        :param bool use_admin_endpoint: if True, will use the /api/admin
            endpoint to retrieve the metadata value else will use the vanilla
            /api endpoint.

        :return: an object containing EntityType.METADATA_VALUE XML data which
            represents the metadata value corresponding to the provided key and
            domain.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: AccessForbiddenException: If there is no metadata entry
            corresponding to the key provided.
        """
        if not isinstance(domain, MetadataDomain):
            raise InvalidParameterException('Invalid domain.')

        if not use_admin_endpoint:
            href = self.href
        else:
            href = get_admin_href(self.href)

        metadata_entry_href = \
            f"{href}/{domain.value}/{key}"

        return self.client.get_resource(metadata_entry_href)

    def remove_metadata(self,
                        key,
                        domain=MetadataDomain.GENERAL,
                        use_admin_endpoint=False):
        """Remove a metadata entry.

        :param str key: key of the metadata to be removed.
        :param client.MetadataDomain domain: domain of the entry to be removed.

        :return: an object of type EntityType.TASK XML which represents
            the asynchronous task that is deleting the metadata entry.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: AccessForbiddenException: If there is no metadata entry
            corresponding to the key provided.

        :raises: MissingLinkException: If the remove link is missing from the
            XML representation of the metadata entry. This error most likely
            indicates that the wrong api endpoint was used viz. /api instead of
            /api/admin.
        """
        metadata_value = self.get_metadata_value(
            key=key,
            domain=domain,
            use_admin_endpoint=use_admin_endpoint)

        return self.client.delete_linked_resource(metadata_value,
                                                  RelationType.REMOVE, None)
