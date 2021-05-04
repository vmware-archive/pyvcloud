# VMware vCloud Director Python SDK
# Copyright (c) 2014-2021 VMware, Inc. All Rights Reserved.
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

from pyvcloud.vcd.client import E_VMEXT
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.exceptions import EntityNotFoundException
from pyvcloud.vcd.extension import Extension


class NSXTExtension():
    def __init__(self, client):
        self.client = client
        self.extension = Extension(client)
        self.resource = None

    def reload(self):
        """Reloads the resource representation of the extension.

        This method should be called in between two method invocations on the
        Extension object, if the former call changes the representation of the
        Extension in vCD.
        """
        self.resource = self.client.get_linked_resource(
            self.extension.get_resource(), RelationType.DOWN,
            EntityType.NETWORK_MANAGERS.value)

    def get_resource(self):
        """Fetches the XML representation of /api/admin/extension/nsxtManagers.

        :return: object containing EntityType.EXTENSION XML data representing
            the endpoint.
        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.reload()
        return self.resource

    def get(self, name):
        """Retrieve info of a NSX-T Manager.

        :param str name: name of the NSX-T Manager whose info
        we want to retrieve.
        :return: an object containing EntityType.USER XML data
            describing the named NSX-T Manager.
        :rtype: lxml.objectify.ObjectifiedElement
        """
        nsxt_managers = self.client.get_linked_resource(
            self.get_resource(), RelationType.ADD,
            EntityType.NSXT_MANAGER.value)

        if not hasattr(nsxt_managers, 'NsxTManager'):
            msg = "No NSX-T Managers are registered yet."
            raise EntityNotFoundException(msg)

        for nsxt_manager in nsxt_managers.NsxTManager:
            if nsxt_manager.get('name') == name:
                return nsxt_manager

        msg = f"No NSX-T Managers found with name '{name}'."
        raise EntityNotFoundException(msg)

    def list(self):
        """List all of available NSX-T Managers.

        :return: an object containing EntityType.USER XML data describing
            NSX-T Managers.
        :rtype: lxml.objectify.ObjectifiedElement
        """
        nsxt_managers = self.client.get_linked_resource(
            self.get_resource(), RelationType.ADD,
            EntityType.NSXT_MANAGER.value)

        if not hasattr(nsxt_managers, 'NsxTManager'):
            msg = "No NSX-T Managers are registered yet."
            raise EntityNotFoundException(msg)

        return nsxt_managers.NsxTManager

    def add(self, name, url, username, password):
        """Add NSX-T Manager with vCD.

        :param str name: name of the NSX-T Manager.
        :param str url: NSX-T Manager URL Endpoint
        :param str username: NSX-T Manager user name
        :param str password: NSX-T Manager password

        :rtype: lxml.objectify.ObjectifiedElement
        """
        nsxtManagerParams = E_VMEXT.NsxTManager(
            E_VMEXT.Username(username),
            E_VMEXT.Password(password),
            E_VMEXT.Url(url),
            name=name)
        return self.client.post_linked_resource(self.get_resource(),
                                                RelationType.ADD,
                                                EntityType.NSXT_MANAGER.value,
                                                nsxtManagerParams)

    def delete(self, name):
        """Delete NSX-T Manager from vCD.

        :param str name: name of the NSX-T Manager to delete.
        """
        nsxt_manager = self.get(name)
        return self.client.delete_linked_resource(
            nsxt_manager, RelationType.REMOVE, EntityType.NSXT_MANAGER.value)

    def update(self, name,
               new_name=None,
               url=None,
               username=None,
               password=None):
        """Update the connected NSX-T Manager.

        :param str name: name of the NSX-T Manager.
        :param str new_name: name of the NSX-T Manager
        :param str url: NSX-T Manager URL Endpoint
        :param str username: NSX-T Manager user name
        :param str password: NSX-T Manager password

        :rtype: lxml.objectify.ObjectifiedElement
        """
        nsxt_manager = self.get(name)
        new_name = new_name or name
        nsxtManagerParams = E_VMEXT.NsxTManager(name=new_name)
        if username:
            nsxtManagerParams['Username'] = E_VMEXT.Username(username)
        if password:
            nsxtManagerParams['Password'] = E_VMEXT.Password(password)
        if url:
            nsxtManagerParams['Url'] = E_VMEXT.Url(url)

        return self.client.put_linked_resource(nsxt_manager,
                                               RelationType.EDIT,
                                               EntityType.NSXT_MANAGER.value,
                                               nsxtManagerParams)
