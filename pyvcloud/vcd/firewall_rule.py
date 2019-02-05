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
from pyvcloud.vcd.client import create_element
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.exceptions import InvalidParameterException
from pyvcloud.vcd.gateway import Gateway
from pyvcloud.vcd.gateway_services import GatewayServices
from pyvcloud.vcd.network_url_constants import FIREWALL_RULE_URL_TEMPLATE
from pyvcloud.vcd.network_url_constants import FIREWALL_RULES_URL_TEMPLATE
from pyvcloud.vcd.network_url_constants import FIREWALL_URL_TEMPLATE


class FirewallRule(GatewayServices):
    __SOURCE = 'source'
    __DESTINATION = 'destination'
    __GROUP_OBJECT_LIST = ['securitygroup', 'ipset', 'virtualmachine',
                           'network']
    __VNIC_GROUP_LIST = ['gatewayinterface']

    def _build_self_href(self, rule_id):
        rule_href = (self.network_url + FIREWALL_RULE_URL_TEMPLATE).format(
            rule_id)
        self.href = rule_href

    def _extract_id(self, rule_href):
        rule_id_index = rule_href.index(FIREWALL_RULES_URL_TEMPLATE) + \
            len(FIREWALL_RULES_URL_TEMPLATE) + 1
        return rule_href[rule_id_index:]

    def __config_url(self):
        config_index = self.href.index(FIREWALL_URL_TEMPLATE)
        return self.href[:config_index] + FIREWALL_URL_TEMPLATE

    def _reload(self):
        """Reloads the resource representation of the Firewall rule."""
        self.resource = \
            self.client.get_resource(self.href)

    def delete(self):
        """Delete a Firewall rule from gateway."""
        self._get_resource()
        return self.client.delete_resource(self.href)

    def edit(self, source_values=None, destination_values=None):
        """Edit a Firewall rule.

        :param list source_values: list of source values. e.g.,
        [value:value_type]
        :param list destination_values: list of destination values. e.g.,
        [value:value_type]
        """
        self._get_resource()
        self.validate_types(source_values, FirewallRule.__SOURCE)
        self.validate_types(destination_values, FirewallRule.__DESTINATION)
        firewall_rule_temp = self.resource

        if source_values:
            if not hasattr(firewall_rule_temp, FirewallRule.__SOURCE):
                firewall_rule_temp.append(create_element(
                    FirewallRule.__SOURCE))
            if not hasattr(firewall_rule_temp.source, 'exclude'):
                firewall_rule_temp.source.append(create_element('exclude',
                                                                False))
            self._populate_objects_info(firewall_rule_temp, source_values,
                                        FirewallRule.__SOURCE)
        if destination_values:
            if not hasattr(firewall_rule_temp, FirewallRule.__DESTINATION):
                firewall_rule_temp.append(create_element(
                    FirewallRule.__DESTINATION))
            if not hasattr(firewall_rule_temp.destination, 'exclude'):
                firewall_rule_temp.destination.append(create_element(
                    'exclude', False))
            self._populate_objects_info(firewall_rule_temp,
                                        destination_values,
                                        FirewallRule.__DESTINATION)

        self.client.put_resource(self.href, firewall_rule_temp,
                                 EntityType.DEFAULT_CONTENT_TYPE.value)

    def _populate_objects_info(self, firewall_rule_temp, values, type):
        """It will mutate firewall_rule_temp.

        :param firewall_rule_temp: Firewall rule object resource
        :param list values: list of values
        :param str type: type. e.g., source, destination
        """
        for value in values:
            values_arr = value.split(':')
            object_type = values_arr[1]
            object = values_arr[0]
            if type == FirewallRule.__SOURCE:
                firewall_rule_temp.source.append(self._get_group_element(
                    type, object_type, object))
            if type == FirewallRule.__DESTINATION:
                firewall_rule_temp.destination.append(
                    self._get_group_element(type, object_type, object))

    def _get_group_element(self, type, object_type, value):
        """Get group element base upon the type and object type.

        :param str type: It can be source/destination
        :param str object_type: Possible values for this would be
        'gatewayinterface','virtualmachine','network', 'ipset',
        'securitygroup', 'ip'
        :param str value: value
        :return: group objectified element
        :rtype: :rtype: lxml.objectify.ObjectifiedElement
        """
        if object_type == 'ip':
            return create_element('ipAddress', value)
        gateway_res = Gateway(self.client, resource=self.parent)
        object_list = gateway_res.list_firewall_objects(type, object_type)
        for object in object_list:
            if object_type in FirewallRule.__GROUP_OBJECT_LIST:
                return self.__find_element(object, value, 'groupingObjectId')
            elif object_type in FirewallRule.__VNIC_GROUP_LIST:
                return self.__find_element(object, value, 'vnicGroupId')

    def __find_element(self, object, value, group_type):
        """Find element in the properties using group type.

        :param dict object: dict of values
        :param str value: value
        :param str group_type: group type. e.g., groupingObjectId
        """
        if object.get('name') == value:
            properties = object.get('prop')
            for prop in properties:
                if prop.get('name') == group_type:
                    return create_element(group_type, prop.get('value'))

    def validate_types(self, source_types, type):
        """Validate input param for valid type.

        :param list source_types: list of value:value_type. e.g.,
        ExtNw:gatewayinterface
        :param str type: It can be source/destination
        :raise: InvalidParameterException: exception if input param is not
        valid.
        """
        if source_types:
            valid_type_list = ['gatewayinterface', 'virtualmachine', 'network',
                               'ipset', 'securitygroup', 'ip']
            for source_type in source_types:
                if source_type.lower() == 'any':
                    continue
                source_type_arr = source_type.split(':')
                if len(source_type_arr) <= 1:
                    raise InvalidParameterException(
                        type + " type should be in the format of "
                               "value:value_type. for ex: "
                               "ExtNw:gatewayinterface")
                valid_type = source_type_arr[1]
                if valid_type not in valid_type_list:
                    valid_type_list_str = ','.join(valid_type_list)
                    raise InvalidParameterException(
                        valid_type + " param is not valid. It should be "
                                     "from " + valid_type_list_str)
