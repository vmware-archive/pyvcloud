# VMware vCloud Director Python SDK
# Copyright (c) 2014-2019 VMware, Inc. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
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
from pyvcloud.vcd.vapp_services import VappServices


class VappFirewall(VappServices):
    def enable_firewall_service(self, isEnable):
        """Enable Firewall service to vApp network.

        :param bool isEnable: True for enable and False for Disable.
        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is updating the vApp network.
        :rtype: lxml.objectify.ObjectifiedElement
        :raises: InvalidParameterException: Enable firewall service failed as
            given network's connection is not routed
        """
        self._get_resource()
        fence_mode = self.resource.Configuration.FenceMode
        if fence_mode != 'natRouted':
            raise InvalidParameterException(
                "Enable firewall service failed as given network's connection "
                "is not routed")
        firewall = self.resource.Configuration.Features.FirewallService
        if isEnable:
            firewall.IsEnabled = E.IsEnabled(True)
        else:
            firewall.IsEnabled = E.IsEnabled(False)
        return self.client.put_linked_resource(
            self.resource, RelationType.EDIT, EntityType.vApp_Network.value,
            self.resource)
