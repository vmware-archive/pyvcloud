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
from pyvcloud.vcd.gateway_services import GatewayServices
from pyvcloud.vcd.network_url_constants import DHCP_POOL_URL_TEMPLATE
from pyvcloud.vcd.network_url_constants import DHCP_POOLS
from pyvcloud.vcd.network_url_constants import DHCP_POOLS_URL_TEMPLATE


class DhcpPool(GatewayServices):

    def _build_self_href(self, pool_id):
        pool_href = (self.network_url + DHCP_POOL_URL_TEMPLATE).format(pool_id)
        self.href = pool_href

    def _extract_id(self, dhcp_pool_href):
        pool_id_index = dhcp_pool_href.index(DHCP_POOLS_URL_TEMPLATE) + \
            len(DHCP_POOLS_URL_TEMPLATE) + 1
        return dhcp_pool_href[pool_id_index:]

    def __config_url(self):
        pool_id_length = len(DHCP_POOLS + '/' + str(self.resource_id))
        return self.href[:-pool_id_length]

    def _reload(self):
        """Reloads the resource representation of the DHCP pool."""
        pool_config_resource = \
            self.client.get_resource(self.__config_url())
        ip_pools = pool_config_resource.ipPools
        for pool in ip_pools.ipPool:
            if pool.poolId == self.resource_id:
                self.resource = pool
                break

    def get_pool_info(self):
        """Get the details of DHCP pool.

        :return: Dictionary having DHCP Pool details.
        e.g.
        {'ID': 196609, 'IPRange': '2.2.3.7-2.2.3.10', 'DomainName':
         'abc.com', 'DefaultGateway': '2.2.3.1', 'PrimaryNameServer':
         '2.2.3.10', 'SecondaryNameServer': '2.2.3.12', 'LeaseTime': '8640',
         'SubnetMask': 255.255.255.0, 'AllowHugeRange': False}
        :rtype: Dictionary
        """
        pool_info = {}
        resource = self._get_resource()
        pool_info['ID'] = resource.poolId
        pool_info['IPRange'] = resource.ipRange
        if hasattr(resource, 'domainName'):
            pool_info['DomainName'] = resource.domainName
        if hasattr(resource, 'defaultGateway'):
            pool_info['DefaultGateway'] = resource.defaultGateway
        if hasattr(resource, 'primaryNameServer'):
            pool_info['PrimaryNameServer'] = resource.primaryNameServer
        if hasattr(resource, 'secondaryNameServer'):
            pool_info['secondaryNameServer'] = resource.secondaryNameServer

        pool_info['LeaseTime'] = resource.leaseTime

        if hasattr(resource, 'subnetMask'):
            pool_info['SubnetMask'] = resource.subnetMask
        if hasattr(resource, 'allowHugeRange'):
            pool_info['AllowHugeRange'] = resource.allowHugeRange
        return pool_info

    def delete_pool(self):
        """Delete a DHCP Pool from gateway."""
        self._get_resource()
        return self.client.delete_resource(self.href)
