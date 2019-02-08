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
            if int(rule.ruleId) == int(self.rule_id):
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

    def get_nat_rule_info(self):
        """Get the details of nat rule.

        :return: Dictionary having nat rule details.
        e.g.
        {'ID': 196609, 'OriginalAddress': '2.2.3.7', 'OriginalPort':
         'any', 'TranslatedAddress': '2.2.3.8', 'TranslatedPort':
         'any', 'Action': 'snat', 'Protocol': 'any', 'Enabled': True,
         'Logging': False, 'Description': ''}
        :rtype: Dictionary
        """
        nat_rule_info = {}
        self.get_resource()
        nat_rule = self.resource
        nat_rule_info['ID'] = nat_rule.ruleId
        nat_rule_info['OriginalAddress'] = nat_rule.originalAddress
        nat_rule_info['OriginalPort'] = nat_rule.originalPort
        nat_rule_info['TranslatedAddress'] = nat_rule.translatedAddress
        nat_rule_info['TranslatedPort'] = nat_rule.translatedPort
        nat_rule_info['Action'] = nat_rule.action
        nat_rule_info['Protocol'] = nat_rule.protocol
        nat_rule_info['Enabled'] = nat_rule.enabled
        nat_rule_info['Logging'] = nat_rule.loggingEnabled
        if hasattr(nat_rule, 'description'):
            nat_rule_info['Description'] = nat_rule.description
        return nat_rule_info

    def update_nat_rule(self,
                        original_address=None,
                        translated_address=None,
                        description=None,
                        protocol=None,
                        original_port=None,
                        translated_port=None,
                        icmp_type=None,
                        logging_enabled=None,
                        enabled=None,
                        vnic=None):
        """Update a Nat Rule.

        param original_address str: original IP address
        param translated_address str: translated IP address
        param description str: nat rule description
        param protocol str: protocol such as tcp/udp/icmp
        param original_port: port no. such as FTP(21)
        param translated_port: port no. such as HTTP(80)
        param icmp_type str: icmp type such as "Echo-request"
        param logging_enabled bool: enable logging
        param enable bool: enable nat rule
        param int vnic: interface of gateway

        """
        nat_rule = self.get_resource()

        if original_address is not None:
            nat_rule.originalAddress = E.originalAddress(original_address)
        if translated_address is not None:
            nat_rule.translatedAddress = \
                E.translatedAddress(translated_address)
        if description is not None:
            nat_rule.description = E.description(description)
        if protocol is not None:
            nat_rule.protocol = E.protocol(protocol)
        if original_port is not None:
            nat_rule.originalPort = E.originalPort(original_port)
        if translated_port is not None:
            nat_rule.translatedPort = E.translatedPort(translated_port)
        if icmp_type is not None:
            nat_rule.icmpType = E.icmpType(icmp_type)
        if logging_enabled is not None:
            nat_rule.loggingEnabled = E.loggingEnabled(logging_enabled)
        if enabled is not None:
            nat_rule.enabled = E.enabled(enabled)
        if vnic is not None:
            nat_rule.vnic = E.vnic(vnic)

        return self.client.put_resource(
            self.href,
            nat_rule,
            EntityType.DEFAULT_CONTENT_TYPE.value)
