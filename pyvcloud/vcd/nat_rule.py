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
from pyvcloud.vcd.network_url_constants import NAT_RULE_URL_TEMPLATE
from pyvcloud.vcd.network_url_constants import NAT_RULES
from pyvcloud.vcd.network_url_constants import NAT_RULES_URL_TEMPLATE
from pyvcloud.vcd.utils import build_network_url_from_gateway_url


class NatRule(object):
    def __init__(self, client, gateway_name=None, rule_id=None,
                 nat_href=None, resource=None):
        """Constructor for Nat objects.

        :param pyvcloud.vcd.client.Client client: the client that will be used
            to make REST calls to vCD.
        :param str gateway_name: name of the gateway entity.
        :param str rule_id: nat rule id.
        :param str nat_href: nat rule href.
        :param lxml.objectify.ObjectifiedElement resource: object containing
            EntityType.NAT XML data representing the nat rule.
        """
        self.client = client
        self.gateway_name = gateway_name
        self.rule_id = rule_id
        if gateway_name is not None and \
           rule_id is not None and \
           nat_href is None and \
           resource is None:
            self.__build_self_href()
        if nat_href is None and resource is None and self.href is None:
            raise InvalidParameterException(
                "NatRule initialization failed as arguments are either "
                "invalid or None")
        if nat_href is not None:
            self.rule_id = self.__extract_rule_id(nat_href)
            self.href = nat_href
        self.resource = resource

    def __build_self_href(self):
        self.parent = self.get_parent_by_name()
        self.parent_href = self.parent.get('href')
        network_url = build_network_url_from_gateway_url(self.parent_href)
        self.href = (network_url + NAT_RULE_URL_TEMPLATE).format(self.rule_id)

    def __extract_rule_id(self, nat_href):
        self.rule_id = nat_href
        rule_id_index = nat_href.index(NAT_RULES_URL_TEMPLATE) \
            + len(NAT_RULES_URL_TEMPLATE) + 1
        self.rule_id = nat_href[rule_id_index:]

    def get_resource(self):
        """Fetches the XML representation of the nat rule.

        :return: object containing EntityType.NAT_RULE XML data
        representing the Nat Rule.
        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.reload()
        return self.resource

    def reload(self):
        """Reloads the resource representation of the nat rule."""
        rule_id_length = len(NAT_RULES + '/' + str(self.rule_id))
        nat_rule_config_url = self.href[:-rule_id_length]
        nat_rules_config_resource = \
            self.client.get_resource(nat_rule_config_url)
        nat_rules = nat_rules_config_resource.natRules.natRule
        for rule in nat_rules:
            if rule.ruleId == self.rule_id:
                self.resource = rule
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

    def delete_nat_rule(self):
        """Delete a nat rule from gateway."""
        self.get_resource()
        return self.client.delete_resource(self.href)
