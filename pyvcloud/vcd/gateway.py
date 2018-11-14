# VMware vCloud Director Python SDK
# Copyright (c) 2014-2018 VMware, Inc. All Rights Reserved.
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
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.exceptions import InvalidParameterException
from pyvcloud.vcd.utils import get_admin_href


class Gateway(object):
    def __init__(self, client, name=None, href=None, resource=None):
        """Constructor for Gateway objects.

        :param pyvcloud.vcd.client.Client client: the client that will be used
            to make REST calls to vCD.
        :param str name: name of the entity.
        :param str href: URI of the entity.
        :param lxml.objectify.ObjectifiedElement resource: object containing
            EntityType.EDGE_GATEWAY XML data representing the gateway.
        """
        self.client = client
        self.name = name
        if href is None and resource is None:
            raise InvalidParameterException(
                "Gateway initialization failed as arguments are either "
                "invalid or None")
        self.href = href
        self.resource = resource
        if resource is not None:
            self.name = resource.get('name')
            self.href = resource.get('href')
        self.href_admin = get_admin_href(self.href)

    def get_resource(self):
        """Fetches the XML representation of the gateway from vCD.

        Will serve cached response if possible.

        :return: object containing EntityType.EDGE_GATEWAY XML data
        representing the gateway.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.reload()
        return self.resource

    def reload(self):
        """Reloads the resource representation of the gateway.

        This method should be called in between two method invocations on the
        Gateway object, if the former call changes the representation of the
        gateway in vCD.
        """
        self.resource = self.client.get_resource(self.href)
        if self.resource is not None:
            self.name = self.resource.get('name')
            self.href = self.resource.get('href')

    def convert_to_advanced(self):
        """Convert to advanced gateway.

        :return: object containing EntityType.TASK XML data representing the
            asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement

        """
        if self.resource is None:
            self.reload()

        return self.client.post_linked_resource(self.resource,
                                                RelationType.
                                                CONVERT_TO_ADVANCED_GATEWAY,
                                                None, None)

    def enable_distributed_routing(self, enable=True):
        """Enable Distributed Routing.

        :param bool enable: True if user want to enable else False.

        :return: object containing EntityType.TASK XML data
            representing the asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.reload()
        gateway = self.resource
        current_dr_status = gateway.Configuration.DistributedRoutingEnabled
        if enable == current_dr_status:
            return
        gateway.Configuration.DistributedRoutingEnabled = \
            E.DistributedRoutingEnabled(enable)
        return self.client.put_linked_resource(self.resource,
                                               RelationType.EDIT,
                                               EntityType.EDGE_GATEWAY.value,
                                               gateway)
