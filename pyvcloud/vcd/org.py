# VMware vCloud Director Python SDK
# Copyright (c) 2014-2018 VMware, Inc. All Rights Reserved.
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

import math
import os
import shutil
import tarfile
import tempfile
import time
import traceback
import urllib

from lxml import etree
from lxml import objectify

from pyvcloud.vcd.acl import Acl
from pyvcloud.vcd.client import ApiVersion
from pyvcloud.vcd.client import E
from pyvcloud.vcd.client import E_OVF
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import find_link
from pyvcloud.vcd.client import get_links
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import QueryResultFormat
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.client import ResourceType
from pyvcloud.vcd.exceptions import DownloadException
from pyvcloud.vcd.exceptions import EntityNotFoundException
from pyvcloud.vcd.exceptions import InvalidParameterException
from pyvcloud.vcd.exceptions import UploadException
from pyvcloud.vcd.system import System
from pyvcloud.vcd.utils import get_admin_href
from pyvcloud.vcd.utils import get_safe_members_in_tar_file
from pyvcloud.vcd.utils import to_dict

# Uptil pyvcloud v20.0.0 1 MB was the default chunk size,
# in constrast vCD H5 UI uses 50MB for upload chunk size,
# 10MB is a happy medium between 50MB and 1MB.
DEFAULT_CHUNK_SIZE = 10 * 1024 * 1024


class Org(object):
    def __init__(self, client, href=None, resource=None):
        """Constructor for Org objects.

        :param pyvcloud.vcd.client.Client client: the client that will be used
            to make REST calls to vCD.
        :param str href: URI of the entity.
        :param lxml.objectify.ObjectifiedElement resource: object
            containing EntityType.ORG XML data representing the organization.
        """
        self.client = client
        if href is None and resource is None:
            raise InvalidParameterException('Org initialization failed as '
                                            'arguments are either invalid '
                                            'or None')
        self.href = href
        self.resource = resource
        if resource is not None:
            self.href = resource.get('href')
        self.href_admin = get_admin_href(self.href)

    def reload(self):
        """Reloads the resource representation of the organization.

        This method should be called in between two method invocations on the
        Org object, if the former call changes the representation of the
        organization in vCD.
        """
        self.resource = self.client.get_resource(self.href)

    def get_name(self):
        """Retrieves the name of the organization.

        :return: name of the organization.

        :rtype: str
        """
        if self.resource is None:
            self.reload()
        return self.resource.get('name')

    def create_catalog(self, name, description):
        """Create a catalog in the organization.

        :param str name: name of the catalog to be created.
        :param str description: description of the catalog to be created.

        :return: an object containing EntityType.ADMIN_CATALOG XML data
            representing a sparsely populated catalog element.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.reload()
        payload = E.AdminCatalog(E.Description(description), name=name)
        return self.client.post_linked_resource(
            self.resource, RelationType.ADD, EntityType.ADMIN_CATALOG.value,
            payload)

    def delete_catalog(self, name):
        """Delete a catalog in the organization.

        :param str name: name of the catalog to be deleted.

        :raises: EntityNotFoundException: if the named catalog can not be
            found.
        :raises: sub-class of VcdResponseException: if the REST call is not
            successful.
        """
        catalog_admin_resource = self.get_catalog(name=name,
                                                  is_admin_operation=True)
        self.client.delete_linked_resource(
            catalog_admin_resource, RelationType.REMOVE, media_type=None)

    def list_catalogs(self):
        """List all catalogs in the organization.

        :return: a list of dictionaries, where each item contains information
            about a catalog in the organization.

        :rtype: list
        """
        if self.client.is_sysadmin():
            resource_type = ResourceType.ADMIN_CATALOG.value
        else:
            resource_type = ResourceType.CATALOG.value
        result = []
        q = self.client.get_typed_query(
            resource_type, query_result_format=QueryResultFormat.ID_RECORDS)
        records = list(q.execute())
        for r in records:
            result.append(
                to_dict(
                    r,
                    resource_type=resource_type,
                    exclude=['owner', 'org']))
        return result

    def get_catalog(self, name, is_admin_operation=False):
        """Retrieves a catalog by name.

        :param str name: name of the catalog to be retrieved.
        :param bool is_admin_operation: if set True, will return the admin
            view of the catalog.

        :return: an object containing EntityType.CATALOG or
            EntityType.ADMIN_CATALOG XML data representing the catalog.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: EntityNotFoundException: if the named catalog can not be
            found.
        """
        if self.resource is None:
            self.reload()
        links = get_links(
            self.resource,
            rel=RelationType.DOWN,
            media_type=EntityType.CATALOG.value)
        for link in links:
            if name == link.name:
                if is_admin_operation:
                    href = get_admin_href(link.href)
                else:
                    href = link.href
                return self.client.get_resource(href)
        raise EntityNotFoundException('Catalog not found (or)'
                                      ' Access to resource is forbidden')

    def update_catalog(self, old_catalog_name, new_catalog_name, description):
        """Update the name and/or description of a catalog.

        :param str old_catalog_name: current name of the catalog.
        :param str new_catalog_name: new name of the catalog.
        :param str description: new description of the catalog.

        :return: an object containing EntityType.ADMIN_CATALOG XML data
            describing the updated catalog.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: EntityNotFoundException: if the named catalog can not be
            found.
        """
        admin_catalog_resource = self.get_catalog(
            old_catalog_name, is_admin_operation=True)
        if new_catalog_name is not None:
            admin_catalog_resource.set('name', new_catalog_name)
        if description is not None:
            admin_catalog_resource['Description'] = E.Description(description)
        return self.client.put_linked_resource(
            admin_catalog_resource,
            rel=RelationType.EDIT,
            media_type=EntityType.ADMIN_CATALOG.value,
            contents=admin_catalog_resource)

    def share_catalog(self, name, share=True):
        """Share a catalog with all org-admins of all organizations.

        This operation can be performed by only System Administrators.

        :param str name: name of the catalog to be shared.

        :raises: EntityNotFoundException: if the named catalog can not be
            found.
        """
        # The link to publish catalog was moved to /api/catalog/{id}'s body in
        # vCD 9.1 (api v30.0). In previous versions the link to share catalog
        # was present in the /api/admin/catalog/{id}'s body.
        # Currently the lowest supported vCD api version is 29.0, which is the
        # only version for which we need to look in /api/admin/catalog/{id}'s
        # body while trying to share a catalog.
        # TODO() remove this conditional logic once we stop supporting api
        # version 29.0.
        if self.client.get_api_version() == ApiVersion.VERSION_29.value:
            catalog_resource = self.get_catalog(name, is_admin_operation=True)
        else:
            catalog_resource = self.get_catalog(name)

        is_published = 'true' if share else 'false'
        params = E.PublishCatalogParams(E.IsPublished(is_published))

        return self.client.post_linked_resource(
            resource=catalog_resource,
            rel=RelationType.PUBLISH,
            media_type=EntityType.PUBLISH_CATALOG_PARAMS.value,
            contents=params)

    def change_catalog_owner(self, catalog_name, user_name):
        """Change the ownership of catalog to a given user.

        This operation can be performed by only users with admin privileges.

        :param str catalog_name: name of the catalog whose ownership needs
            to be changed
        :param str user_name: name of the new owner of the catalog
        """
        catalog_admin_resource = self.get_catalog(
            catalog_name, is_admin_operation=True)

        new_user_resource = self.get_user(user_name)

        owner_resource = catalog_admin_resource.Owner
        owner_resource.User.set('href', new_user_resource.get('href'))
        objectify.deannotate(owner_resource)

        return self.client.put_linked_resource(
            resource=catalog_admin_resource,
            rel=RelationType.DOWN,
            media_type=EntityType.OWNER.value,
            contents=owner_resource)

    def list_catalog_items(self, name):
        """Retrieve all items in a catalog.

        :param str name: name of the catalog whose items need to be retrieved.

        :return: a list of dictionaries. Each dict object contains 'name' and
            'id' of an item in the catalog.

        :rtype: dict

        :raises: EntityNotFoundException: if the named catalog can not be
            found.
        """
        catalog_resource = self.get_catalog(name)
        items = []
        for item in catalog_resource.CatalogItems.getchildren():
            items.append({'name': item.get('name'), 'id': item.get('id')})
        return items

    def get_catalog_item(self, name, item_name):
        """Retrieve an item in a catalog.

        :param str name: name of the catalog whose item needs to be retrieved.
        :param str item_name: name of the item which needs to be retrieved.

        :return: an object containing EntityType.MEDIA or
            EntityTYPE.VAPP_TEMPLATE XML data describing the entity
            corresponding to the catalog item.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: EntityNotFoundException: if the catalog/named item can not be
            found.
        """
        catalog_resource = self.get_catalog(name)
        for item in catalog_resource.CatalogItems.getchildren():
            if item.get('name') == item_name:
                return self.client.get_resource(item.get('href'))
        raise EntityNotFoundException('Catalog item not found.')

    def delete_catalog_item(self, name, item_name):
        """Delete an item from a catalog.

        :param str name: name of the catalog whose item needs to be deleted.
        :param str item_name: name of the item which needs to be deleted.

        :raises: EntityNotFoundException: if the catalog/named item can not be
            found.
        """
        catalog_resource = self.get_catalog(name)
        for item in catalog_resource.CatalogItems.getchildren():
            if item.get('name') == item_name:
                self.client.delete_resource(item.get('href'))
                return
        raise EntityNotFoundException('Catalog item not found.')

    def _is_enable_download_required(self, entity_resource, item_type):
        """Helper method to determine need for download enabling.

        :param lxml.objectify.ObjectifiedElement entity_resource: an object
            containing EntityType.MEDIA or EntityType.VAPP_TEMPLATE XML data
            describing the entity corresponding to the catalog item which
            needs to be downloaded.
        :param str item_type: type of entity we are trying to enable for
            download. Valid values are EntityType.VAPP_TEMPLATE and
            EntityType.MEDIA.

        return: True, if the entity needs to be enabled for download else
            False.

        :rtype: bool
        """
        enable_download_required = True
        if item_type == EntityType.MEDIA.value:
            if hasattr(entity_resource, 'Files'):
                enable_download_required = False
        elif item_type == EntityType.VAPP_TEMPLATE.value:
            ovf_download_link = find_link(entity_resource,
                                          RelationType.DOWNLOAD_DEFAULT,
                                          EntityType.TEXT_XML.value, False)
            if ovf_download_link is not None:
                enable_download_required = False

        return enable_download_required

    def _enable_download(self, entity_resource, task_callback):
        """Helper method to enable an entity for download.

        Behind the scene it involves vCD copying the template/media file
        from ESX hosts to spool area (transfer folder).

        :param lxml.objectify.ObjectifiedElement entity_resource: an object
            containing EntityType.MEDIA or EntityType.VAPP_TEMPLATE XML data
            describing the entity corresponding to the catalog item which
            needs to be downloaded.
        :param function task_callback: a function with signature
            function(task) to let the caller monitor the progress of enable
            download task.

        return: Nothing
        """
        task = self.client.post_linked_resource(
            entity_resource, RelationType.ENABLE, None, None)
        self.client.get_task_monitor().wait_for_success(
            task, 60, 1, callback=task_callback)

    def download_catalog_item(self,
                              catalog_name,
                              item_name,
                              file_name,
                              chunk_size=DEFAULT_CHUNK_SIZE,
                              callback=None,
                              task_callback=None):
        """Downloads an item from a catalog into a local file.

        :param str catalog_name: name of the catalog whose item needs to be
            downloaded.
        :param str item_name: name of the item which needs to be downloaded.
        :param str file_name: name of the target file on local disk where the
            contents of the catalog item will be downloaded to.
        :param int chunk_size: size of chunks in which the catalog item will
            be downloaded and written to the disk.
        :param function callback: a function with signature
            function(bytes_written, total_size) to let the caller monitor
            progress of the download operation.
        :param function task_callback: a function with signature
            function(task) to let the caller monitor the progress of enable
            download task.

        :return: number of bytes written to file.

        :rtype: int

        :raises: EntityNotFoundException: if the catalog/named item is not
            found.
        """
        item_resource = self.get_catalog_item(catalog_name, item_name)
        item_type = item_resource.Entity.get('type')
        entity_resource = self.client.get_resource(
            item_resource.Entity.get('href'))

        if self._is_enable_download_required(entity_resource, item_type):
            self._enable_download(entity_resource, task_callback)
            entity_resource = self.client.get_resource(
                entity_resource.get('href'))

        bytes_written = 0
        if item_type == EntityType.MEDIA.value:
            size = entity_resource.Files.File.get('size')
            download_href = entity_resource.Files.File.Link.get('href')
            bytes_written = self.client.download_from_uri(
                download_href,
                file_name,
                chunk_size=chunk_size,
                size=size,
                callback=callback)
        elif item_type == EntityType.VAPP_TEMPLATE.value:
            bytes_written = self._download_ovf(entity_resource, file_name,
                                               chunk_size, callback)
        return bytes_written

    def _download_ovf(self, entity_resource, file_name, chunk_size, callback):
        """Helper method to download an ova file from vCD catalog.

        :param lxml.objectify.ObjectifiedElement entity_resource: an object
            containing EntityType.MEDIA or EntityType.VAPP_TEMPLATE XML data
            describing the entity corresponding to the catalog item which
            needs to be downloaded.
        :param str file_name: name of the target file on local disk where
            the contents of the catalog item will be downloaded to.
        :param int chunk_size: size of chunks in which the catalog item will
            be downloaded and written to the disk.
        :param function callback: a function with signature
            function(bytes_written, total_size) to let the caller monitor
            progress of the download operation.

        :return: number of bytes written to file.

        :rtype: int
        """
        ovf_descriptor = self.client.get_linked_resource(
            entity_resource, RelationType.DOWNLOAD_DEFAULT,
            EntityType.TEXT_XML.value)

        ovf_descriptor_uri = find_link(entity_resource,
                                       RelationType.DOWNLOAD_DEFAULT,
                                       EntityType.TEXT_XML.value).href
        transfer_uri_base = ovf_descriptor_uri.rsplit('/', 1)[0] + '/'

        tempdir = None
        cwd = os.getcwd()
        try:
            tempdir = tempfile.mkdtemp(dir='.')
            ovf_file = os.path.join(tempdir, 'descriptor.ovf')
            with open(ovf_file, 'wb') as f:
                payload = etree.tostring(
                    ovf_descriptor,
                    pretty_print=True,
                    xml_declaration=True,
                    encoding='utf-8')
                f.write(payload)

            ns = '{' + NSMAP['ovf'] + '}'
            files_to_tar = []
            for f in ovf_descriptor.References.File:
                source_file_name = f.get(ns + 'href')
                source_file_size = int(f.get(ns + 'size'))

                # TODO() Add support for ns + 'chunkSize' - will need support
                # for downloading part of a file at an offset from an uri.

                target_file = os.path.join(tempdir, source_file_name)
                uri = transfer_uri_base + source_file_name
                num_bytes = self.client.download_from_uri(
                    uri,
                    target_file,
                    chunk_size=chunk_size,
                    size=str(source_file_size),
                    callback=callback)
                if num_bytes != source_file_size:
                    raise DownloadException(
                        'Download incomplete for file %s' % source_file_name)
                files_to_tar.append(source_file_name)

            with tarfile.open(file_name, 'w') as tar:
                os.chdir(tempdir)
                tar.add('descriptor.ovf')
                for f in files_to_tar:
                    tar.add(f)
        finally:
            if tempdir is not None:
                os.chdir(cwd)
                bytes_written = 0
                if os.path.exists(file_name):
                    stat_info = os.stat(file_name)
                    bytes_written = stat_info.st_size
                shutil.rmtree(tempdir)

        return bytes_written

    def upload_media(self,
                     catalog_name,
                     file_name,
                     item_name=None,
                     description='',
                     chunk_size=DEFAULT_CHUNK_SIZE,
                     callback=None):
        """Uploads a media file to a catalog.

        This method only uploads bits to vCD spool area, doesn't block while
        vCD imports the uploaded bit into catalog.

        :param str catalog_name: name of the catalog where the media file will
            be uploaded.
        :param str file_name: name of the media file on local disk which will
            be uploaded.
        :param str item_name: this param lets us rename the media file once
            uploaded to the catalog.If this param is not specified, the
            catalog item will share the same name as the media file being
            uploaded.
        :param int chunk_size: size of chunks in which the file will be
            uploaded to the catalog.
        :param function callback: a function with signature
            function(bytes_written, total_size) to let the caller monitor
            progress of the upload operation.

        :return: number of bytes uploaded to the catalog.

        :rtype: int

        :raises: EntityNotFoundException: if the catalog is not found.
        :raises: InternalServerException: if item already exists in catalog.
        """
        stat_info = os.stat(file_name)
        catalog_resource = self.get_catalog(catalog_name)
        if item_name is None:
            item_name = os.path.basename(file_name)
        image_type = os.path.splitext(item_name)[1][1:]
        media = E.Media(
            name=item_name, size=str(stat_info.st_size), imageType=image_type)
        media.append(E.Description(description))
        catalog_item_resource = self.client.post_linked_resource(
            catalog_resource, RelationType.ADD, EntityType.MEDIA.value, media)
        entity_resource = self.client.get_resource(
            catalog_item_resource.Entity.get('href'))
        file_href = entity_resource.Files.File.Link.get('href')
        return self._upload_file(
            file_name, file_href, chunk_size=chunk_size, callback=callback)

    def upload_ovf(self,
                   catalog_name,
                   file_name,
                   item_name=None,
                   description='',
                   chunk_size=DEFAULT_CHUNK_SIZE,
                   callback=None):
        """Uploads an ova file to a catalog.

        This method only uploads bits to vCD spool area, doesn't block while
        vCD imports the uploaded bit into catalog.

        :param str catalog_name: name of the catalog where the ova file will
            be uploaded.
        :param str file_name: name of the ova file on local disk which will be
            uploaded.
        :param str item_name: this param let's us rename the ova file once
            uploaded to the catalog. If this param is not specified, the
            catalog item will share the same name as the ova file being
            uploaded.
        :param int chunk_size: size of chunks in which the file will be
            uploaded to the catalog.
        :param function callback: a function with signature
            function(bytes_written, total_size) to let the caller monitor
            progress of the upload operation.

        :return: number of bytes uploaded to the catalog.

        :rtype: int

        :raises: EntityNotFoundException: if the catalog is not found.
        :raises: InternalServerException: if item already exists in catalog.
        """
        catalog_resource = self.get_catalog(catalog_name)
        if item_name is None:
            item_name = os.path.basename(file_name)
        total_bytes_uploaded = 0

        try:
            tempdir = tempfile.mkdtemp(dir='.')
            ova = tarfile.open(file_name)
            ova.extractall(path=tempdir,
                           members=get_safe_members_in_tar_file(ova))
            ova.close()
            ovf_file = None
            extracted_files = os.listdir(tempdir)
            for f in extracted_files:
                fn, ex = os.path.splitext(f)
                if ex == '.ovf':
                    ovf_file = os.path.join(tempdir, f)
                    break
            if ovf_file is None:
                raise UploadException('OVF descriptor file not found.')

            stat_info = os.stat(ovf_file)
            total_bytes_uploaded += stat_info.st_size
            ovf_resource = objectify.parse(ovf_file)
            files_to_upload = []
            ns = '{' + NSMAP['ovf'] + '}'
            for f in ovf_resource.getroot().References.File:
                source_file = {
                    'href': f.get(ns + 'href'),
                    'name': f.get(ns + 'id'),
                    'size': f.get(ns + 'size'),
                    'chunkSize': f.get(ns + 'chunkSize')
                }
                files_to_upload.append(source_file)

            params = E.UploadVAppTemplateParams(name=item_name)
            params.append(E.Description(description))
            catalog_item_resource = self.client.post_linked_resource(
                catalog_resource, RelationType.ADD,
                EntityType.UPLOAD_VAPP_TEMPLATE_PARAMS.value, params)

            entity_href = catalog_item_resource.Entity.get('href')
            entity_resource = self.client.get_resource(entity_href)
            ovf_upload_href = entity_resource.Files.File.Link.get('href')
            self.client.put_resource(ovf_upload_href, ovf_resource,
                                     EntityType.TEXT_XML.value)

            while True:
                time.sleep(5)
                entity_resource = self.client.get_resource(entity_href)
                if len(entity_resource.Files.File) > 1:
                    break

            for source_file in files_to_upload:
                source_file_name = source_file.get('href')
                source_file_size = source_file.get('size')
                target_uri = None
                for target_file in entity_resource.Files.File:
                    if source_file_name == target_file.get('name'):
                        target_uri = target_file.Link.get('href')
                        break
                if target_uri is None:
                    raise UploadException('Couldn\'t find uri to upload'
                                          ' file %s' % source_file_name)

                if source_file['chunkSize'] is not None:
                    file_paths = self._get_multi_part_file_paths(
                        tempdir, source_file_name, int(source_file_size),
                        int(source_file['chunkSize']))
                    total_bytes_uploaded += self._upload_multi_part_file(
                        file_paths, target_uri, chunk_size, callback)
                else:
                    file_path = os.path.join(tempdir, source_file_name)
                    total_bytes_uploaded += self._upload_file(
                        file_path,
                        target_uri,
                        chunk_size=chunk_size,
                        callback=callback)
        except Exception as e:
            print(traceback.format_exc())
            raise UploadException('Ovf upload failed').with_traceback(
                e.__traceback__)
        finally:
            shutil.rmtree(tempdir)

        return total_bytes_uploaded

    def _get_multi_part_file_paths(self, base_dir, base_file_name,
                                   total_file_size, part_size):
        """Helper method to get path to multi-part files.

        For example a file called test.vmdk with total_file_size = 100 bytes
        and part_size = 40 bytes, implies the file is made of *3* part
        files.
            - test.vmdk.000000000 = 40 bytes
            - test.vmdk.000000001 = 40 bytes
            - test.vmdk.000000002 = 20 bytes
        Say base_dir = '/dummy_path/', and base_file_name = 'test.vmdk' then
        the output of this function will be ['/dummy_path/test.vmdk.000000000',
        '/dummy_path/test.vmdk.000000001', '/dummy_path/test.vmdk.000000002',]

        :param str base_dir: base directory where the file parts are located.
        :param str base_file_name: common portion of the filename among all
            the part-files.
        :param int total_file_size: size of the entire file (sum of all
            parts).
        :param int part_size: size of each part of the file.

        :return: a list of file-paths as strings, where each item corresponds
            to one part of the multi-part file.

        :rtype: list
        """
        file_paths = []
        num_parts = math.ceil(total_file_size / part_size)
        for i in range(num_parts):
            postfix = ('000000000' + str(i))[-9:]
            file_path = os.path.join(base_dir, base_file_name + '.' + postfix)
            file_paths.append(file_path)

        return file_paths

    def _upload_file(self,
                     file_name,
                     target_uri,
                     chunk_size=DEFAULT_CHUNK_SIZE,
                     callback=None):
        """Helper function to upload contents of a local file.

        :param str file_name: name of the file on local disk whose content
            will be uploaded to the uri.
        :param str target_uri: uri where the contents of the local file will
            be uploaded to.
        :param int chunk_size: size of chunks in which the local file will be
            uploaded.
        :param function callback: a function with signature
            function(bytes_written, total_size) to let the caller monitor
            progress of the upload operation.

        :return: number of bytes uploaded to the uri.

        :rtype: int
        """
        return self._upload_part_file(
            file_name, target_uri, chunk_size=chunk_size, callback=callback)

    def _upload_multi_part_file(self,
                                part_file_paths,
                                target_uri,
                                chunk_size=DEFAULT_CHUNK_SIZE,
                                callback=None):
        """Helper function to upload contents of a multi-part local file.

        :param list(str) part_file_paths: the path (with name) of the parts of
            the file on local disk whose content will be uploaded to the uri.
        :param str target_uri: uri where the contents of the local file will
            be uploaded to.
        :param int chunk_size: size of chunks in which the local file will be
            uploaded.
        :param function callback: a function with signature
            function(bytes_written, total_size) to let the caller monitor
            progress of the upload operation.

        :return: number of bytes uploaded to the uri.

        :rtype: int
        """
        total_bytes_to_upload = 0
        for part_file in part_file_paths:
            stat_info = os.stat(part_file)
            total_bytes_to_upload += stat_info.st_size

        uploaded_bytes = 0
        for part_file_name in part_file_paths:
            uploaded_bytes += self._upload_part_file(
                part_file_name, target_uri, uploaded_bytes,
                total_bytes_to_upload, chunk_size, callback)
        return uploaded_bytes

    def _upload_part_file(self,
                          part_file_path,
                          target_uri,
                          offset=0,
                          total_file_size=None,
                          chunk_size=DEFAULT_CHUNK_SIZE,
                          callback=None):
        """Helper function to upload contents of a single part file.

        :param list(str) part_file_path: path (with name) of the part-file on
            local disk whose content will be uploaded to the uri.
        :param str target_uri: uri where the contents of the local part-file
            will be uploaded to.
        :param int offset: number of bytes to skip on the target uri while
            uploading contents of the part-file.
        :param int total_file_size: sum total of all parts of the file that
            is being uploaded.
        :param int chunk_size: size of chunks in which the local file will be
            uploaded.
        :param function callback: a function with signature
            function(bytes_written, total_size) to let the caller monitor
            progress of the upload operation.

        :return: number of bytes uploaded to the uri.

        :rtype: int
        """
        stat_info = os.stat(part_file_path)
        part_file_size = stat_info.st_size
        if total_file_size is None:
            total_file_size = part_file_size
        uploaded_bytes = 0

        with open(part_file_path, 'rb') as f:
            while uploaded_bytes < part_file_size:
                data = f.read(chunk_size)
                data_size = len(data)
                if data_size <= chunk_size:
                    range_str = 'bytes %s-%s/%s' % \
                                (offset + uploaded_bytes,
                                 offset + uploaded_bytes + data_size - 1,
                                 total_file_size)
                    response = self.client.upload_fragment(
                        target_uri, data, range_str)
                    uploaded_bytes += data_size
                    if callback is not None:
                        callback(offset + uploaded_bytes, total_file_size)

                    # We can hit an issue similar to the following issue
                    # https://github.com/requests/requests/issues/4664
                    #
                    # Our uploads would fail with the error message,
                    #
                    # urllib3.exceptions.ProtocolError: ('Connection aborted.',
                    # ConnectionResetError(10054, 'An existing connection was
                    # forcibly closed by the remote host', None, 10054, None))
                    #
                    # This error is probably caused by request lib reusing
                    # keep-alive connections that were marked as closed by the
                    # server. As a workaround for this, we will wait 1 second
                    # after issuing the PUT call if the connection is closed by
                    # the server. Spacing out the requests seems to help
                    # requests lib with pruning dead keep-alive connections.
                    if self.client.is_connection_closed(response):
                        time.sleep(1)
        return uploaded_bytes

    def capture_vapp(self,
                     catalog_resource,
                     vapp_href,
                     catalog_item_name,
                     description,
                     customize_on_instantiate=False,
                     overwrite=False):
        """Capture vApp as a template into a catalog.

        :param lxml.objectify.ObjectifiedElement catalog_resource: an object
            containing EntityType.CATALOG XML data representing the catalog to
            which we will add the new template.
        :param str vapp_href: href of the vApp to capture.
        :param str catalog_item_name: name of the target catalog item.
        :param str description: description of the catalog item.
        :param bool customize_on_instantiate: flag indicating if the vApp to
            be instantiated from this vApp template can be customized.
        :param bool overwrite: flag indicating if the item in the catalog has
            to be overwritten if it already exists. If it doesn't exist, this
            flag is not used.

        :return: an object containing EntityType.VAPP_TEMPLATE XML data
            describing the captured template.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        contents = E.CaptureVAppParams(
            E.Description(description),
            E.Source(href=vapp_href),
            name=catalog_item_name)
        if customize_on_instantiate:
            contents.append(
                E.CustomizationSection(
                    E_OVF.Info('VApp template customization section'),
                    E.CustomizeOnInstantiate('true')))
        if overwrite:
            try:
                item = self.get_catalog_item(
                    catalog_resource.get('name'), catalog_item_name)
                contents.append(
                    E.TargetCatalogItem(
                        href=item.get('href'),
                        id=item.get('id'),
                        type=item.get('type'),
                        name=item.get('name')))
            except Exception:
                pass
        return self.client.post_linked_resource(
            catalog_resource,
            rel=RelationType.ADD,
            media_type=EntityType.CAPTURE_VAPP_PARAMS.value,
            contents=contents)

    def create_user(self,
                    user_name,
                    password,
                    role_href,
                    full_name='',
                    description='',
                    email='',
                    telephone='',
                    im='',
                    alert_email='',
                    alert_email_prefix='',
                    stored_vm_quota=0,
                    deployed_vm_quota=0,
                    is_group_role=False,
                    is_default_cached=False,
                    is_external=False,
                    is_alert_enabled=False,
                    is_enabled=False):
        """Create a new user in the current organization.

        :param str user_name: username of the new user.
        :param str password: password of the new user (must be at least 6
            characters long).
        :param str role_href: href of the role for the new user.
        :param str full_name: full name of the user.
        :param str description: description for the user.
        :param str email: email address of the user.
        :param str telephone: The telephone of the user.
        :param str im: instant message address of the user.
        :param str alert_email: email address where alerts should be sent.
        :param str alert_email_prefix: string to prepend to alert message
            subject line.
        :param str stored_vm_quota: quota of vApps that this user can store.
        :param str deployed_vm_quota: quota of vApps that this user can deploy
            concurrently.
        :param bool is_group_role: indicates if the user has a group role.
        :param bool is_default_cached: indicates if user should be cached.
        :param bool is_external: indicates if user is imported from an external
            source.
        :param bool is_alert_enabled: if, True will enable email alert for the
            user.
        :param bool is_enabled: if True, will enable the user after creation
            else will let the user remain disabled after creation.

        :return: an object containing EntityType.USER XML data describing the
            user that just got created.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        resource_admin = self.client.get_resource(self.href_admin)
        user = E.User(
            E.Description(description),
            E.FullName(full_name),
            E.EmailAddress(email),
            E.Telephone(telephone),
            E.IsEnabled(is_enabled),
            E.IM(im),
            E.IsAlertEnabled(is_alert_enabled),
            E.AlertEmailPrefix(alert_email_prefix),
            E.AlertEmail(alert_email),
            E.IsExternal(is_external),
            E.IsDefaultCached(is_default_cached),
            E.IsGroupRole(is_group_role),
            E.StoredVmQuota(stored_vm_quota),
            E.DeployedVmQuota(deployed_vm_quota),
            E.Role(href=role_href),
            E.Password(password),
            name=user_name)
        return self.client.post_linked_resource(
            resource_admin, RelationType.ADD, EntityType.USER.value, user)

    def update_user(self, user_name, is_enabled=None, role_name=None):
        """Update an user.

        :param str user_name: username of the user.
        :param bool is_enabled: True, to enable the user, False to disable the
            user.
        :param str role_name: name of the role being assigned to user.

        :return: an object containing EntityType.USER XML data describing the
            user that just got updated.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        user = self.get_user(user_name)
        if is_enabled is not None:
            if hasattr(user, 'IsEnabled'):
                user['IsEnabled'] = E.IsEnabled(is_enabled)
        if role_name:
            if hasattr(user, 'Role'):
                role = self.get_role_record(role_name)
                user['Role'] = E.Role(href=role.get('href'))

        if is_enabled or role_name:
            return self.client.put_resource(
                user.get('href'), user, EntityType.USER.value)

        return user

    def get_user(self, user_name):
        """Retrieve info of an user in current organization.

        :param str user_name: name of the user whose info we want to retrieve.

        :return: an object containing EntityType.USER XML data describing the
            named user.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        user_record = list(self.list_users(('name', user_name)))

        if len(user_record) < 1:
            raise EntityNotFoundException(
                'User \'%s\' does not exist.' % user_name)
        return self.client.get_resource(user_record[0].get('href'))

    def list_users(self, name_filter=None):
        """Retrieve the list of users in the current organization.

        :param 2-tuple name_filter: filters retrieved users by name. First item
            in the tuple needs to be the string 'name' and the second item
            should be the value of the filter.

        :return: user data in form of lxml.objectify.ObjectifiedElement
            objects, which contains QueryResultUserRecordType XML data.

        :rtype: generator object
        """
        if self.resource is None:
            self.reload()
        resource_type = ResourceType.USER.value
        org_filter = None
        if self.client.is_sysadmin():
            resource_type = ResourceType.ADMIN_USER.value
            org_filter = 'org==%s' % \
                urllib.parse.quote_plus(self.resource.get('href'))
        query = self.client.get_typed_query(
            resource_type,
            query_result_format=QueryResultFormat.RECORDS,
            equality_filter=name_filter,
            qfilter=org_filter)

        return query.execute()

    def delete_user(self, user_name):
        """Deletes an user from the current organization.

        This operation needs admin privileges.

        :param str user_name: name of the user to be deleted.
        """
        user = self.get_user(user_name)
        return self.client.delete_resource(user.get('href'))

    def create_role(self, role_name, description, rights):
        """Creates a role in the organization.

        :param str role_name: name of the role to be created.
        :param str description: description of the role.
        :param tuple rights: names (as str) of zero or more rights to be
            associated with the role.

        :return: an object containing EntityType.ROLE XML data describing the
            role just created.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        org_admin_resource = self.client.get_resource(self.href_admin)
        role = E.Role(
            E.Description(description), E.RightReferences(), name=role_name)
        if rights is None:
            rights = ()
        for right in tuple(rights):
            right_record = self.get_right_record(right)
            role.RightReferences.append(
                E.RightReference(
                    name=right_record.get('name'),
                    href=right_record.get('href'),
                    type=EntityType.RIGHT.value))
        return self.client.post_linked_resource(
            org_admin_resource, RelationType.ADD, EntityType.ROLE.value, role)

    def delete_role(self, name):
        """Deletes specified role from the organization.

        :param str name: name of the role to be deleted.
        """
        if self.resource is None:
            self.reload()
        role_record = self.get_role_record(name)
        self.client.delete_resource(role_record.get('href'))

    def get_role_resource(self, role_name):
        """Retrieves XML resource of a given role.

        :param str role_name: name of the role to be retrieved.

        :return: an object containing EntityType.ROLE XML data representing the
            role.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        role_record = self.get_role_record(role_name)
        return self.client.get_resource(role_record.get('href'))

    def get_role_record(self, role_name):
        """Retrieve role record with a particular name in the current org.

        :param str role_name: name of the role object to be retrieved.

        :return: role record.

        :rtype: dict

        :raises: EntityNotFoundException: if role with the given name is not
            found.
        """
        role_record = self.list_roles(('name', role_name))
        if len(role_record) < 1:
            raise EntityNotFoundException(
                'Role \'%s\' does not exist.' % role_name)
        return role_record[0]

    def list_roles(self, name_filter=None):
        """Retrieve the list of roles in the current organization.

        :param tuple name_filter: (tuple): filter roles by name. The first item
            in the tuple must be the string 'name' and the second item should
            be value of the filter as a str.

        :return: dict objects, each object representing a single role.
            record.

        :rtype: list
        """
        if self.resource is None:
            self.reload()

        org_filter = None
        resource_type = ResourceType.ROLE.value

        if self.client.is_sysadmin():
            resource_type = ResourceType.ADMIN_ROLE.value
            org_filter = 'org==%s' % \
                urllib.parse.quote_plus(self.resource.get('href'))

        query = self.client.get_typed_query(
            resource_type,
            query_result_format=QueryResultFormat.RECORDS,
            equality_filter=name_filter,
            qfilter=org_filter)
        result = []
        for r in list(query.execute()):
            result.append(
                to_dict(
                    r, resource_type=resource_type, exclude=['org',
                                                             'orgName']))
        return result

    def add_rights(self, rights):
        """Adds set of rights to the organization.

        :param tuple rights: names of rights as strings.

        :return: an object containing EntityType.ORG_RIGHTS XML data
            representing the updated rights in the organization.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        org_admin_resource = self.client.get_resource(self.href_admin)
        org_rights = E.OrgRights()
        for right in rights:
            right_record = self.get_right_record(right)
            org_rights.append(
                E.RightReference(
                    name=right_record.get('name'),
                    href=right_record.get('href'),
                    type=EntityType.RIGHT.value))
        return self.client.post_linked_resource(
            org_admin_resource.RightReferences, RelationType.ADD,
            EntityType.ORG_RIGHTS.value, org_rights)

    def remove_rights(self, rights):
        """Removes set of rights from the organization.

        :param tuple rights: names of rights as strings.

        :return: an object containing EntityType.ORG_RIGHTS XML data
            representing the updated rights in the organization.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        org_admin_resource = self.client.get_resource(self.href_admin)
        org_rights_resource = None
        if hasattr(org_admin_resource, 'RightReferences'):
            org_rights_resource = self.client.get_resource(
                org_admin_resource.RightReferences.get('href'))
            if hasattr(org_rights_resource, 'RightReference'):
                for right in rights:
                    for right_reference in \
                            list(org_rights_resource.RightReference):
                        if right_reference.get('name') == right:
                            org_rights_resource.remove(right_reference)
                            break
                return self.client.put_linked_resource(
                    org_admin_resource.RightReferences, RelationType.EDIT,
                    EntityType.ORG_RIGHTS.value, org_rights_resource)
        return org_rights_resource

    def get_right_resource(self, right_name):
        """Retrieves resource of a given right.

        :param str right_name: name of the right.

        :return: an object containing EntityType.RIGHT XML data representing
            the right.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        right_record = self.get_right_record(right_name)
        return self.client.get_resource(right_record.get('href'))

    def get_right_record(self, right_name):
        """Retrieves corresponding record of the specified right.

        :param str right_name: name of the right record to be retrieved.

        :return: right record

        :rtype: dict
        """
        right_record = self.list_rights_available_in_system(('name',
                                                             right_name))
        if len(right_record) < 1:
            raise EntityNotFoundException(
                'Right \'%s\' does not exist.' % right_name)
        return right_record[0]

    def list_rights_available_in_system(self, name_filter=None):
        """Retrieves all rights available in the System organization.

        :param tuple name_filter: (tuple): filter rights by name. The first
            item in the tuple must be the string 'name' and the second item
            should be value of the filter as a str.

        :return: rights as a list of dictionaries, where each dictionary
            contains information about a single right.

        :rtype: list
        """
        if self.resource is None:
            self.reload()

        resource_type = ResourceType.RIGHT.value
        query = self.client.get_typed_query(
            resource_type,
            query_result_format=QueryResultFormat.RECORDS,
            equality_filter=name_filter)
        records = list(query.execute())
        result = []
        if len(records) > 0:
            for r in records:
                result.append(
                    to_dict(r, resource_type=resource_type, exclude=[]))
        return result

    def list_rights_of_org(self):
        """Retrieves the list of rights associated with the current org.

        :return: rights as a list of dictionaries, where each dictionary
            contains information about a single right.

        :rtype: list
        """
        org_admin_resource = self.client.get_resource(self.href_admin)
        rights = []
        if hasattr(org_admin_resource, 'RightReferences') and \
                hasattr(org_admin_resource.RightReferences, 'RightReference'):
            for right_reference in \
                    org_admin_resource.RightReferences.RightReference:
                rights.append(to_dict(right_reference, exclude=['type']))
        return rights

    def get_catalog_access_settings(self, catalog_name):
        """Retrieve the access settings of a catalog.

        :param str catalog_name: name of the catalog.

        :return: an object containing EntityType.CONTROL_ACCESS_PARAMS XML data
            representing the Access Control List of the catalog.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        catalog_resource = self.get_catalog(name=catalog_name)
        acl = Acl(self.client, catalog_resource)
        return acl.get_access_settings()

    def add_catalog_access_settings(self,
                                    catalog_name,
                                    access_settings_list=None):
        """Add access settings to a particular catalog.

        :param str catalog_name: name of the catalog to which access settings
            needs to be added.
        :param list access_settings_list: list of access_setting in the dict
            format. Each dict contains:

            - type: (str): type of the subject. Value must be either 'org'
                or 'user'.
            - name: (str): name of the user or organization.
            - access_level: (str): access_level of the particular subject.
                Acceptable values are 'ReadOnly', 'Change' or 'FullControl'

        :return: an object containing EntityType.CONTROL_ACCESS_PARAMS XML data
            representing the updated Access Control List of the catalog.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        catalog_resource = self.get_catalog(name=catalog_name)
        acl = Acl(self.client, catalog_resource)
        return acl.add_access_settings(access_settings_list)

    def remove_catalog_access_settings(self,
                                       catalog_name,
                                       access_settings_list=None,
                                       remove_all=False):
        """Remove access settings from a particular catalog.

        :param str catalog_name: name of the catalog from which access_settings
            need to be removed.
        :param list access_settings_list: list of access_setting in the dict
            format. Each dict contains,

            - type: (str): type of the subject. Value must be either 'org'
                or 'user'.
            - name: (str): name of the user or organization.
        :param bool remove_all: True, if all access settings of the catalog
            should be removed.

        :return: an object containing EntityType.CONTROL_ACCESS_PARAMS XML data
            representing the updated Access Control List of the catalog.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        catalog_resource = self.get_catalog(name=catalog_name)
        acl = Acl(self.client, catalog_resource)
        return acl.remove_access_settings(access_settings_list, remove_all)

    def share_catalog_with_org_members(self,
                                       catalog_name,
                                       everyone_access_level='ReadOnly'):
        """Share a catalog with all members of an organization.

        :param str catalog_name: name of the catalog which needs to be shared.
        :param str everyone_access_level: access level when sharing the catalog
            with everyone. Acceptable values are 'ReadOnly', 'Change', or
            'FullControl'. Default value is 'ReadOnly'.

        :return: an object containing EntityType.CONTROL_ACCESS_PARAMS XML data
            representing the updated Access Control List of the catalog.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        catalog_resource = self.get_catalog(name=catalog_name)
        acl = Acl(self.client, catalog_resource)
        return acl.share_with_org_members(everyone_access_level)

    def unshare_catalog_with_org_members(self, catalog_name):
        """Unshare a catalog from all members of the current organization.

        :param str catalog_name: name of the catalog which needs to be unshared
            from everyone.

        :return: an object containing EntityType.CONTROL_ACCESS_PARAMS XML data
            representing the updated Access Control List of the catalog.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        catalog_resource = self.get_catalog(name=catalog_name)
        acl = Acl(self.client, catalog_resource)
        return acl.unshare_from_org_members()

    def update_org(self, is_enabled=None):
        """Update an organization to enable/disable it.

        This operation can only be performed by an user with admin privileges.

        :param bool is_enabled: flag to enable/disable the organization.

        :return: an object containing EntityType.ADMIN_ORG XML data
            representing the updated organization.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        org_admin_resource = self.client.get_resource(self.href_admin)
        if is_enabled is not None:
            if hasattr(org_admin_resource, 'IsEnabled'):
                org_admin_resource['IsEnabled'] = E.IsEnabled(is_enabled)
                return self.client.put_resource(self.href_admin,
                                                org_admin_resource,
                                                EntityType.ADMIN_ORG.value)
        return org_admin_resource

    def create_org_vdc(self,
                       vdc_name,
                       provider_vdc_name,
                       description='',
                       allocation_model='AllocationVApp',
                       cpu_units='MHz',
                       cpu_allocated=0,
                       cpu_limit=0,
                       mem_units='MB',
                       mem_allocated=0,
                       mem_limit=0,
                       nic_quota=0,
                       network_quota=0,
                       vm_quota=0,
                       storage_profiles=[],
                       resource_guaranteed_memory=None,
                       resource_guaranteed_cpu=None,
                       vcpu_in_mhz=None,
                       is_thin_provision=None,
                       network_pool_name=None,
                       uses_fast_provisioning=None,
                       over_commit_allowed=None,
                       vm_discovery_enabled=None,
                       is_enabled=True):
        """Create an Organization VDC in the current organization.

        :param str vdc_name: name of the new org vdc.
        :param str provider_vdc_name: (str): The name of an existing provider
            vdc.
        :param str description: description of the new org vdc.
        :param str allocation_model: allocation model used by this vdc.
            Accepted values are 'AllocationVApp', 'AllocationPool' or
            'ReservationPool'.
        :param str cpu_units: unit for compute capacity allocated to this vdc.
            Accepted values are 'MHz' or 'GHz'.
        :param int cpu_allocated: capacity that is committed to be available.
        :param int cpu_limit: capacity limit relative to the value specified
            for allocation.
        :param str mem_units: unit for memory capacity allocated to this vdc.
            Acceptable values are 'MB' or 'GB'.
        :param int mem_allocated: memory capacity that is committed to be
            available.
        :param int mem_limit: memory capacity limit relative to the value
            specified for allocation.
        :param int nic_quota: maximum number of virtual NICs allowed in this
            vdc. Defaults to 0, which specifies an unlimited number.
        :param int network_quota: maximum number of network objects that can be
            deployed in this vdc. Defaults to 0, which means no networks can be
            deployed.
        :param int vm_quota: maximum number of VMs that can be created in this
            vdc. Defaults to 0, which specifies an unlimited number.
        :param list storage_profiles: list of provider vdc storage profiles to
            add to this vdc. Each item is a dictionary that should include the
            following elements:

            - name: (str): name of the PVDC storage profile.
            - enabled: (bool): True if the storage profile is enabled for
                this vdc.
            - units: (string): Units used to define limit. One of MB or GB.
            - limit: (int): Max number of units allocated for this storage
                profile.
            - default: (bool): True if this is default storage profile for
                this vdc.
        :param float resource_guaranteed_memory: percentage of allocated CPU
            resources guaranteed to vApps deployed in this vdc. Value defaults
            to 1.0 if the element is empty.
        :param float resource_guaranteed_cpu: percentage of allocated memory
            resources guaranteed to vApps deployed in this vdc. Value defaults
            to 1.0 if the element is empty.
        :param int vcpu_in_mhz: specifies the clock frequency, in MegaHertz,
            for any virtual CPU that is allocated to a VM.
        :param bool is_thin_provision: True to request thin provisioning.
        :param str network_pool_name: name to a network pool in the provider
            vdc that this org vdc should use.
        :param bool uses_fast_provisioning: True to request fast provisioning.
        :param bool over_commit_allowed: False to disallow creation of the VDC
            if the AllocationModel is AllocationPool or ReservationPool and the
            ComputeCapacity specified is greater than what the backing provider
            VDC can supply. Defaults to True, if empty or missing.
        :param bool vm_discovery_enabled: True, if discovery of vCenter VMs
            is enabled for resource pools backing this vdc.
        :param bool is_enabled: True, if this vdc is enabled for use by the
            organization users.

        :return: an object containing EntityType.VDC XML data describing the
            new VDC.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.reload()
        sys_admin_resource = self.client.get_admin()
        system = System(self.client, admin_resource=sys_admin_resource)
        pvdc = system.get_provider_vdc(provider_vdc_name)
        resource_admin = self.client.get_resource(self.href_admin)
        params = E.CreateVdcParams(
            E.Description(description),
            E.AllocationModel(allocation_model),
            E.ComputeCapacity(
                E.Cpu(
                    E.Units(cpu_units), E.Allocated(cpu_allocated),
                    E.Limit(cpu_limit)),
                E.Memory(
                    E.Units(mem_units), E.Allocated(mem_allocated),
                    E.Limit(mem_limit))),
            E.NicQuota(nic_quota),
            E.NetworkQuota(network_quota),
            E.VmQuota(vm_quota),
            E.IsEnabled(is_enabled),
            name=vdc_name)
        for sp in storage_profiles:
            pvdc_sp = system.get_provider_vdc_storage_profile(sp['name'])
            params.append(
                E.VdcStorageProfile(
                    E.Enabled(sp['enabled']),
                    E.Units(sp['units']),
                    E.Limit(sp['limit']),
                    E.Default(sp['default']),
                    E.ProviderVdcStorageProfile(href=pvdc_sp.get('href'))))
        if resource_guaranteed_memory is not None:
            params.append(
                E.ResourceGuaranteedMemory(resource_guaranteed_memory))
        if resource_guaranteed_cpu is not None:
            params.append(E.ResourceGuaranteedCpu(resource_guaranteed_cpu))
        if vcpu_in_mhz is not None:
            params.append(E.VCpuInMhz(vcpu_in_mhz))
        if is_thin_provision is not None:
            params.append(E.IsThinProvision(is_thin_provision))
        if network_pool_name is not None:
            npr = system.get_network_pool_reference(network_pool_name)
            href = npr.get('href')
            params.append(
                E.NetworkPoolReference(
                    href=href,
                    id=href.split('/')[-1],
                    type=npr.get('type'),
                    name=npr.get('name')))
        params.append(pvdc)
        if uses_fast_provisioning is not None:
            params.append(E.UsesFastProvisioning(uses_fast_provisioning))
        if over_commit_allowed is not None:
            params.append(E.OverCommitAllowed(over_commit_allowed))
        if vm_discovery_enabled is not None:
            params.append(E.VmDiscoveryEnabled(vm_discovery_enabled))
        return self.client.post_linked_resource(
            resource_admin, RelationType.ADD, EntityType.VDCS_PARAMS.value,
            params)

    def get_vdc(self, name, is_admin_operation=False):
        """Retrieves resource of an org vdc identified by its name.

        :param str name: name of the org vdc to be retrieved.

        :param bool is_admin_operation: if set True, will return the admin
            view of the org vdc resource.

        :return: an object containing EtityType.VDC XML data representing the
            vdc.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: EntityNotFoundException: if the named vdc can not be found.
        """
        if self.resource is None:
            self.reload()
        links = get_links(
            self.resource,
            rel=RelationType.DOWN,
            media_type=EntityType.VDC.value)
        for link in links:
            if name == link.name:
                if is_admin_operation:
                    href = get_admin_href(link.href)
                else:
                    href = link.href
                return self.client.get_resource(href)
        return None

    def list_vdcs(self):
        """List all vdc that are backing the current organization.

        :return: list of dictionaries, where each dictionary contains 'name'
            and 'href' of a vdc in the organization.

        :rtype: list
        """
        if self.resource is None:
            self.reload()
        result = []
        for v in get_links(self.resource, media_type=EntityType.VDC.value):
            result.append({'name': v.name, 'href': v.href})
        return result
