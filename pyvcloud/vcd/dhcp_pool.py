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

from pyvcloud.vcd.client import QueryResultFormat
from pyvcloud.vcd.client import ResourceType
from pyvcloud.vcd.exceptions import EntityNotFoundException
from pyvcloud.vcd.exceptions import InvalidParameterException
from pyvcloud.vcd.exceptions import MultipleRecordsException
from pyvcloud.vcd.network_url_constants import DHCP_URL_TEMPLATE
from pyvcloud.vcd.network_url_constants import DHCP_POOLS
from pyvcloud.vcd.network_url_constants import DHCP_POOLS_URL_TEMPLATE
from pyvcloud.vcd.network_url_constants import DHCP_POOL_URL_TEMPLATE
from pyvcloud.vcd.utils import build_network_url_from_gateway_url


class DhcpPool(object):
    def __init__(self, client, gateway_name=None, pool_id=None,
                 dhcp_pool_href=None, resource=None):
        """Constructor for DHCP objects.
         :param pyvcloud.vcd.client.Client client: the client that will be used
            to make REST calls to vCD.
        :param str gateway_name: name of the gateway entity.
        :param: str pool_id: DHCP IP pool id
        :param str dhcp_pool_href: dhcp href.
        :param lxml.objectify.ObjectifiedElement resource: object containing
            EntityType.DHCP XML data representing the DHCP.
        """
        self.client = client
        self.gateway_name = gateway_name
        if gateway_name is not None and \
                pool_id is not None and \
                dhcp_pool_href is None and \
                resource is None:
            self.pool_id = pool_id
            self.__build_self_href(pool_id)
        if dhcp_pool_href is None and resource is None and self.href is None:
            raise InvalidParameterException(
                "DHCP initialization failed as arguments are either "
                "invalid or None")
        if dhcp_pool_href is not None:
            self.pool_id = self.__extract_pool_id(dhcp_pool_href)
            self.href = dhcp_pool_href
        self.resource = resource

    def __build_self_href(self, pool_id):
        self.parent = self.get_parent_by_name()
        self.parent_href = self.parent.get('href')
        network_url = build_network_url_from_gateway_url(self.parent_href)
        pool_href = (network_url + DHCP_POOL_URL_TEMPLATE).format(pool_id)
        self.href = pool_href

    def __extract_pool_id(self, dhcp_pool_href):
        pool_id_index = dhcp_pool_href.index(DHCP_POOLS_URL_TEMPLATE) \
                        + len(DHCP_POOLS_URL_TEMPLATE) + 1
        return dhcp_pool_href[pool_id_index:]

    def get_resource(self):
        """Fetches the XML representation of the dhcp.
         :return: object containing EntityType.DHCP XML data
        representing the DHCP.
        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.reload()
        return self.resource

    def reload(self):
        """Reloads the resourcerepresentation of the DHCP pool."""
        pool_id_length = len(DHCP_POOLS + '/' + str(self.pool_id))
        pool_config_url = self.href[:-pool_id_length]
        pool_config_resource = \
            self.client.get_resource(pool_config_url)
        ip_pools = pool_config_resource.ipPools
        for pool in ip_pools.ipPool:
            if pool.poolId == self.pool_id:
                self.resource = pool
                break

    def get_parent_by_name(self):
        """Get a gateway by name.
        :return: gateway​
        :rtype: lxml.objectify.ObjectifiedElement​
        :raises: EntityNotFoundException: if the named gateway can not be
            found.
        :raises: MultipleRecordsException: if more than one gateway with the
            provided name are found.
        """
        name_filter = ('name', self.gateway_name)
        query = self.client.get_typed_query(
            ResourceType.EDGE_GATEWAY.value,
            query_result_format=QueryResultFormat.RECORDS,
            equality_filter=name_filter)
        records = list(query.execute())
        if records is None or len(records) == 0:
            raise EntityNotFoundException(
                'Gateway with name \'%s\' not found.' % self.gateway_name)
        elif len(records) > 1:
            raise MultipleRecordsException("Found multiple gateway named "
                                           "'%s'," % self.gateway_name)
        return records[0]

    def delete_pool(self):
        """Delete a DHCP Pool from gateway."""
        self.get_resource()
        return self.client.delete_resource(self.href)
