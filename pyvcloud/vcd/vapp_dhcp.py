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
from pyvcloud.vcd.vapp_services import VappServices


class VappDhcp(VappServices):
    def _build_self_href(self):
        self.href = self.network_url

    def _reload(self):
        """Reloads the resource representation of the Vapp network."""
        self.resource = self.client.get_resource(self.href)

    def set_dhcp_vapp_network(self, ip_range, default_lease_time,
                              max_lease_time):
        """Enable DHCP to vApp network.

        :param str ip_range: IP range in StartAddress-EndAddress format.
        :param str default_lease_time: default lease time.
        :param str max_lease_time: max lease time
        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is updating the vApp network.
        :rtype: lxml.objectify.ObjectifiedElement
        """
        self._get_resource()
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

    def disable_dhcp_vapp_network(self):
        """Enable DHCP to vApp network.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is updating the vApp network.
        :rtype: lxml.objectify.ObjectifiedElement
        """
        self._get_resource()
        dhcp = self.resource.Configuration.Features.DhcpService
        dhcp.IsEnabled = E.IsEnabled(False)
        return self.client.put_linked_resource(
            self.resource, RelationType.EDIT, EntityType.vApp_Network.value,
            self.resource)
