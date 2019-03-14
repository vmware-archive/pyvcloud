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

from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.vapp_services import VappServices


class VappNwAddress(VappServices):
    def list_ip_allocations(self):
        """List all allocated ip of vApp network.

        :param str network_name: name of vApp network.
        :return: list of IP allocation details.
        e.g.
        [{'Allocation_type':'vsmAllocated','Is_deployed':True,
         'Ip_address':'10.1.2.1'},
         {'Allocation_type':'vmAllocated','Is_deployed': True,
         'Ip_address':'10.1.2.12'}]
        :rtype: list.
        """
        self._get_resource()
        obj = self.client.get_linked_resource(
            self.resource, RelationType.DOWN,
            EntityType.ALLOCATED_NETWORK_ADDRESS.value)
        list_allocated_ip = []
        if hasattr(obj, 'IpAddress'):
            for ip_address in obj.IpAddress:
                dict = {}
                dict['Allocation_type'] = ip_address.get('allocationType')
                dict['Is_deployed'] = ip_address.get('isDeployed')
                if hasattr(ip_address, 'IpAddress'):
                    dict['Ip_address'] = ip_address.IpAddress
                list_allocated_ip.append(dict)
            return list_allocated_ip
