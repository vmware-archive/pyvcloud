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
        """Constructor for vSphere Platform Resources

        :param client:  (pyvcloud.vcd.client): The client.
        """
        self.client = client
        self.extension = Extension(client)

    def list_vcenters(self):
        """List vCenter servers attached to the system.

        :return: (lxml.objectify.ObjectifiedElement): list of vCenter
            resources.
        """
        return self.client.get_linked_resource(
            self.extension.get_resource(),
            RelationType.DOWN,
            EntityType.VIM_SERVER_REFS.value).VimServerReference

    def get_vcenter(self, name):
        """Get a vCenter attached to the system by name.

        :return: (lxml.objectify.ObjectifiedElement): vCenter resource.
        """
        for record in self.list_vcenters():
            if record.get('name') == name:
                return self.client.get_resource(record.get('href'))
        return None
