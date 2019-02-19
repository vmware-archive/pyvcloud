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


class Extension(object):
    def __init__(self, client):
        """Constructor for Extension object.

        :param pyvcloud.vcd.client.Client client: the client that will be used
            to make REST calls to vCD.
        """
        self.client = client
        self.resource = None

    def get_resource(self):
        """Fetches the XML representation of /api/admin/extension endpoint.

        Will serve cached response if possible.

        :return: object containing EntityType.EXTENSION XML data representing
            the endpoint.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.reload()
        return self.resource

    def reload(self):
        """Reloads the resource representation of the extension.

        This method should be called in between two method invocations on the
        Extension object, if the former call changes the representation of the
        Extension in vCD.
        """
        self.resource = self.client.get_extension()
