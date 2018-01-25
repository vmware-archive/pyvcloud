# VMware vCloud Director Python SDK
# Copyright (c) 2018 VMware, Inc. All Rights Reserved.
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
from pyvcloud.vcd.extension import Extension


class Platform(object):
    """Helper class to interact with vSphere Platform resources.

    Attributes:
        client (str): Low level client to connect to vCD.
        extension (:obj:`pyvcloud.vcd.Extension`, optional): It holds an
            Extension object to interact with vCD admin extension.

    """

    def __init__(self, client):
        """Constructor for vSphere Platform Resources.

        :param client:  (pyvcloud.vcd.client): The client.
        """
        self.client = client
        self.extension = Extension(client)

    def list_vcenters(self):
        """List vCenter servers attached to the system.

        :return: (lxml.objectify.ObjectifiedElement): list of vCenter
            references.
        """
        return self.client.get_linked_resource(
            self.extension.get_resource(), RelationType.DOWN,
            EntityType.VIM_SERVER_REFS.value).VimServerReference

    def get_vcenter(self, name):
        """Get a vCenter attached to the system by name.

        :param name: (str): The name of vCenter.

        :return: (lxml.objectify.ObjectifiedElement): vCenter resource.

        :raises: Exception: If the named vCenter cannot be located.
        """
        for record in self.list_vcenters():
            if record.get('name') == name:
                return self.client.get_resource(record.get('href'))
        raise Exception('vCenter \'%s\' not found' % name)

    def list_external_networks(self):
        """List all external networks available in the system.

        :return:  A list of :class:`lxml.objectify.StringElement` objects
            representing the external network references.
        """
        ext_net_refs = self.client.get_linked_resource(
            self.extension.get_resource(), RelationType.DOWN,
            EntityType.EXTERNAL_NETWORK_REFS.value)

        if hasattr(ext_net_refs, 'ExternalNetworkReference'):
            return ext_net_refs.ExternalNetworkReference

        return []

    def get_external_network(self, name):
        """Fetch an external network resource identified by it's name.

        :param name: (str): The name of the external network.

        :return: A :class:`lxml.objectify.StringElement` object representing
            the reference to external network.

        :raises: Exception: If the named external network cannot be located.
        """
        ext_net_refs = self.list_external_networks()
        for ext_net in ext_net_refs:
            if ext_net.get('name') == name:
                return self.client.get_resource(ext_net.get('href'))
        raise Exception('External network \'%s\' not found.' % name)
