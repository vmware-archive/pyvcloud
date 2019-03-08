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


class VappDhcp(VappServices):
    def set_dhcp_service(self, ip_range, default_lease_time, max_lease_time):
        """Set DHCP to vApp network.

        :param str ip_range: IP range in StartAddress-EndAddress format.
        :param str default_lease_time: default lease time.
        :param str max_lease_time: max lease time
        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is updating the vApp network.
        :rtype: lxml.objectify.ObjectifiedElement
        :raises: InvalidParameterException: Set DHCP service failed as given
            network's connection is Direct
        """
        self._get_resource()
        if self.resource.Configuration.FenceMode == 'bridged':
            raise InvalidParameterException(
                "Set DHCP service failed as given network's connection is "
                "Direct")
        ip_ranges = ip_range.split('-')
        if not hasattr(self.resource.Configuration, 'Features'):
            index = self.resource.Configuration.index(
                self.resource.Configuration.GuestVlanAllowed)
            self.resource.Configuration.insert(index, E.Features())
        if not hasattr(self.resource.Configuration.Features, 'DhcpService'):
            self.resource.Configuration.Features.append(E.DhcpService())
        dhcp = self.resource.Configuration.Features.DhcpService
        if hasattr(dhcp, 'IsEnabled'):
            dhcp.IsEnabled = E.IsEnabled(True)
        else:
            dhcp.append(E.IsEnabled(True))
        if hasattr(dhcp, 'DefaultLeaseTime'):
            dhcp.DefaultLeaseTime = E.DefaultLeaseTime(default_lease_time)
        else:
            dhcp.append(E.DefaultLeaseTime(default_lease_time))
        if hasattr(dhcp, 'MaxLeaseTime'):
            dhcp.MaxLeaseTime = E.MaxLeaseTime(max_lease_time)
        else:
            dhcp.append(E.MaxLeaseTime(max_lease_time))
        if hasattr(dhcp, 'IpRange'):
            dhcp.IpRange.StartAddress = E.StartAddress(ip_ranges[0])
            dhcp.IpRange.EndAddress = E.EndAddress(ip_ranges[1])
        else:
            dhcp.append(
                E.IpRange(
                    E.StartAddress(ip_ranges[0]), E.EndAddress(ip_ranges[1])))
        return self.client.put_linked_resource(
            self.resource, RelationType.EDIT, EntityType.vApp_Network.value,
            self.resource)

    def enable_dhcp_service(self, isEnable):
        """Enable DHCP to vApp network.

        :param bool isEnable: True for enable and False for Disable.
        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is updating the vApp network.
        :rtype: lxml.objectify.ObjectifiedElement
        """
        self._get_resource()
        dhcp = self.resource.Configuration.Features.DhcpService
        if isEnable:
            dhcp.IsEnabled = E.IsEnabled(True)
        else:
            dhcp.IsEnabled = E.IsEnabled(False)
        return self.client.put_linked_resource(
            self.resource, RelationType.EDIT, EntityType.vApp_Network.value,
            self.resource)
