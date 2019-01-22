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
from pyvcloud.vcd.network_url_constants import DHCP_POOLS
from pyvcloud.vcd.network_url_constants import DHCP_POOLS_URL_TEMPLATE
from pyvcloud.vcd.network_url_constants import DHCP_POOL_URL_TEMPLATE


class DhcpPool(GatewayServices):

    def build_self_href(self, pool_id):
        pool_href = (self.network_url + DHCP_POOL_URL_TEMPLATE).format(pool_id)
        self.href = pool_href

    def extract_id(self, dhcp_pool_href):
        pool_id_index = dhcp_pool_href.index(DHCP_POOLS_URL_TEMPLATE) \
                        + len(DHCP_POOLS_URL_TEMPLATE) + 1
        return dhcp_pool_href[pool_id_index:]

    def __config_url(self):
        pool_id_length = len(DHCP_POOLS + '/' + str(self.resource_id))
        return self.href[:-pool_id_length]

    def reload(self):
        """Reloads the resource representation of the DHCP pool."""

        pool_config_resource = \
            self.client.get_resource(self.__config_url())
        ip_pools = pool_config_resource.ipPools
        for pool in ip_pools.ipPool:
            if pool.poolId == self.resource_id:
                self.resource = pool
                break

    def delete_pool(self):
        """Delete a DHCP Pool from gateway."""
        self.get_resource()
        return self.client.delete_resource(self.href)
