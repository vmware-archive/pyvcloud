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

from pyvcloud.vcd.client import QueryResultFormat
from pyvcloud.vcd.client import ResourceType
from pyvcloud.vcd.exceptions import EntityNotFoundException


class PortgroupHelper(object):
    """Helper class to get the portgroup details(name, moref or type)"""

    def __init__(self, client):
        """Constructor for PortgroupHelper object.

        :param pyvcloud.vcd.client.Client client: the client that will be used
            to make REST calls to vCD.
        """
        self.client = client

    def get_available_portgroup_name(self, vim_server_name, portgroupType):
        """Fetches portgroup name using portgroup type(DV_PORTGROUP or NETWORK).

        Query uses vCenter Server name as filter and returns the first available
        portgroup

        :param str vim_server_name: vCenter server name
        :param str portgroupType: type of port group
        :return: name of the portgroup
        :rtype: str
        :raises: EntityNotFoundException: if any port group cannot be found.
        """
        name_filter = ('vcName', vim_server_name)
        query = self.client.get_typed_query(
            ResourceType.PORT_GROUP.value,
            query_result_format=QueryResultFormat.RECORDS,
            equality_filter=name_filter)
        pgroup_name = ''
        for record in list(query.execute()):
            if record.get('networkName') == '--':
                if record.get('portgroupType') == portgroupType \
                        and not record.get('name').startswith('vxw-'):
                    pgroup_name = record.get('name')
                    break
        if not pgroup_name:
            raise EntityNotFoundException('port group not found in'
                                          'vCenter : ' + vim_server_name)

        return pgroup_name

    def get_ext_net_portgroup_name(self, vim_server_name, ext_net_name):
        """Fetches portgroup name using portgroup type(DV_PORTGROUP or NETWORK)
         which is used by given external network.

        Query uses vCenter Server name as filter and returns the first available
        portgroup

        :param str vim_server_name: vCenter server name
        :param str ext_net_name: external network name
        :return: name of the portgroup
        :rtype: str
        :raises: EntityNotFoundException: if any port group cannot be found.
        """
        name_filter = ('vcName', vim_server_name)

        query = self.client.get_typed_query(
            ResourceType.PORT_GROUP.value,
            query_result_format=QueryResultFormat.RECORDS,
            equality_filter=name_filter)
        pgroup_name = ''
        for record in list(query.execute()):
            if record.get('networkName') == ext_net_name \
                    and not record.get('name').startswith('vxw-'):
                    pgroup_name = record.get('name')
                    break
        if not pgroup_name:
            raise EntityNotFoundException('port group not found in'
                                          'vCenter : ' + vim_server_name)

        return pgroup_name
