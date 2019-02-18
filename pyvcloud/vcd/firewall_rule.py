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
    __GROUP_OBJECT_LIST = [
        'securitygroup', 'ipset', 'virtualmachine', 'network'
    ]
    __VNIC_GROUP_LIST = ['gatewayinterface']
    __APPLICATION = 'application'
    __SERVICE = 'service'
    __PROTOCOL_LIST = ['tcp', 'udp', 'icmp', 'any']

    def _build_self_href(self, rule_id):
        rule_href = (
            self.network_url + FIREWALL_RULE_URL_TEMPLATE).format(rule_id)
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

    def edit(self,
             source_values=None,
             destination_values=None,
             services=None,
             new_name=None):
        """Edit a Firewall rule.

        :param list source_values: list of source values. e.g.,
        [value:value_type]
        :param list destination_values: list of destination values. e.g.,
        [value:value_type]
        :param list services: protocol to port mapping.
         e.g., [{'tcp' : {'any' : any}}]
        :param str new_name: new name of the firewall rule.
        """
        self._get_resource()
        self.validate_types(source_values, FirewallRule.__SOURCE)
        self.validate_types(destination_values, FirewallRule.__DESTINATION)
        firewall_rule_temp = self.resource

        if source_values:
            if not hasattr(firewall_rule_temp, FirewallRule.__SOURCE):
                firewall_rule_temp.append(
                    create_element(FirewallRule.__SOURCE))
            if not hasattr(firewall_rule_temp.source, 'exclude'):
                firewall_rule_temp.source.append(
                    create_element('exclude', False))
            self._populate_objects_info(firewall_rule_temp, source_values,
                                        FirewallRule.__SOURCE)
        if destination_values:
            if not hasattr(firewall_rule_temp, FirewallRule.__DESTINATION):
                firewall_rule_temp.append(
                    create_element(FirewallRule.__DESTINATION))
            if not hasattr(firewall_rule_temp.destination, 'exclude'):
                firewall_rule_temp.destination.append(
                    create_element('exclude', False))
            self._populate_objects_info(firewall_rule_temp, destination_values,
                                        FirewallRule.__DESTINATION)
        if services:
            if not hasattr(firewall_rule_temp, FirewallRule.__APPLICATION):
                firewall_rule_temp.append(
                    create_element(FirewallRule.__APPLICATION))
            self._populate_services(firewall_rule_temp, services)

        if new_name:
            firewall_rule_temp.name = new_name
        self.client.put_resource(self.href, firewall_rule_temp,
                                 EntityType.DEFAULT_CONTENT_TYPE.value)

    def _populate_services(self, firewall_rule_temp, services):
        """Populates service elements.

        :param firewall_rule_temp: Firewall rule
        :param [] services: protocol to port mapping.
         e.g., [{'tcp' : {'any' : any}}]
        """
        if services:
            for service in services:
                protocol = [k for k in service.keys()][0]
                if protocol not in FirewallRule.__PROTOCOL_LIST:
                    valid_protocols = ', '.join(FirewallRule.__PROTOCOL_LIST)
                    raise InvalidParameterException(
                        protocol + " is not valid. It should be from " +
                        valid_protocols)
                value = service.get(protocol)
                source_port = [port for port in value.keys()][0]
                destination_port = value.get(source_port)
                self.__populate_protocol_elements(firewall_rule_temp, protocol,
                                                  source_port,
                                                  destination_port)

    def __populate_protocol_elements(self, firewall_rule_temp, protocol,
                                     source_port, destination_port):
        """Populate protocol elements. It mutates the firewall rule object.

        :param firewall_rule_temp: Firewall rule obj
        :param protocol: protocol
        :param source_port: source port
        :param destination_port: destination port
        """
        application_tag = firewall_rule_temp.application
        service_tag = create_element('service')
        service_tag.append(create_element('protocol', protocol))
        service_tag.append(create_element('port', destination_port))
        service_tag.append(create_element('sourcePort', source_port))
        if protocol == 'icmp':
            service_tag.append(create_element('icmpType', 'any'))
        application_tag.append(service_tag)

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
                firewall_rule_temp.source.append(
                    self._get_group_element(type, object_type, object))
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

        if object_type in FirewallRule.__GROUP_OBJECT_LIST:
            return self.__find_element(type, object_type, value,
                                       'groupingObjectId')
        elif object_type in FirewallRule.__VNIC_GROUP_LIST:
            return self.__find_element(type, object_type, value, 'vnicGroupId')

    def __find_element(self, type, object_type, value, group_type):
        """Find element in the properties using group type.

        :param str type: It can be source/destination
        :param dict object_type: object types
        :param str value: value
        :param str group_type: group type. e.g., groupingObjectId
        """
        gateway_res = Gateway(self.client, resource=self.parent)
        object_list = gateway_res.list_firewall_objects(type, object_type)
        for object in object_list:
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
            valid_type_list = [
                'gatewayinterface', 'virtualmachine', 'network', 'ipset',
                'securitygroup', 'ip'
            ]
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

    def enable_disable_firewall_rule(self, is_enabled):
        """Enabled disabled firewall rule from gateway.

        :param bool is_enabled: flag to enable/disable the firewall rule.
        """
        current_firewall_status = self._get_resource().enabled
        if is_enabled == current_firewall_status:
            return
        if is_enabled:
            self._get_resource().enabled = True
            return self.client.put_resource(
                self.href, self._get_resource(),
                EntityType.DEFAULT_CONTENT_TYPE.value)
        else:
            self._get_resource().enabled = False
            return self.client.put_resource(
                self.href, self._get_resource(),
                EntityType.DEFAULT_CONTENT_TYPE.value)

    def info_firewall_rule(self):
        """Get the details of firewall rule.

        return: Dictionary having firewall rule details.
        e.g.
        {'Id': 196609, 'Name': 'Test rule', 'Rule type':'user',
        'Enabled':'True','Logging enabled':'True','Action':'Accept'}
        :rtype: Dictionary
        """
        firewall_rule_info = {}
        resource = self._get_resource()
        firewall_rule_info['Id'] = resource.id
        firewall_rule_info['Name'] = resource.name
        firewall_rule_info['Rule type'] = resource.ruleType
        firewall_rule_info['Enabled'] = resource.enabled
        firewall_rule_info['Logging enabled'] = resource.loggingEnabled
        firewall_rule_info['Action'] = resource.action
        return firewall_rule_info

    def list_firewall_rule_source_destination(self, type):
        """Get the list of firewall rule source/destination.

        :param str type: It can be source/destination
        return: dict of firewall rule's source/destination details.
        e.g.
        {'exclude':'True','ipAddress':['10.112.12.12','10.232.1.2'],
        'vnicGroupId':['vse','external','internal','vnic-0'],
        'groupingObjectId':['1f0aab71-6d11-4567-994e-2c090fea7350:ipset',
        'urn:vcloud:network:3ed60402-904f-410d-913c-6da77b43a257:']
        }
        :rtype: dict
        """
        resource = self._get_resource()
        firewall_rule_source_destination = {}
        if hasattr(resource, type):
            if hasattr(resource[type], 'exclude'):
                firewall_rule_source_destination['exclude'] = resource[
                    type].exclude
            if hasattr(resource[type], 'vnicGroupId'):
                firewall_rule_source_destination['vnicGroupId'] = [
                    vnicGroupId for vnicGroupId in resource[type].vnicGroupId
                ]
            if hasattr(resource[type], 'ipAddress'):
                firewall_rule_source_destination['ipAddress'] = [
                    ipAddress for ipAddress in resource[type].ipAddress
                ]
            if hasattr(resource[type], 'groupingObjectId'):
                firewall_rule_source_destination['groupingObjectId'] = [
                    groupingObjectId
                    for groupingObjectId in resource[type].groupingObjectId
                ]
        return firewall_rule_source_destination

    def _build_firewall_rules_href(self):
        return self.network_url + FIREWALL_URL_TEMPLATE

    def update_firewall_rule_sequence(self, index):
        """Change firewall rule's sequence of gateway.

        :param int index: new sequence index of firewall rule.
        """
        index = int(index)
        gateway_res = Gateway(self.client, resource=self.parent)
        firewall_rule = gateway_res.get_firewall_rules()
        resource = self._get_resource()
        for rule in firewall_rule.firewallRules.firewallRule:
            if rule.id == resource.id:
                firewall_rule.firewallRules.remove(rule)
                firewall_rule.firewallRules.insert(index, rule)
                break
        return self.client.put_resource(self._build_firewall_rules_href(),
                                        firewall_rule,
                                        EntityType.DEFAULT_CONTENT_TYPE.value)

    def delete_firewall_rule_source_destination(self, value, type):
        """Delete firewall rule's source/destination value of gateway.

        It will delete all source/destination value of given value.
        :param str value: value to remove from source/destination.
        :param str type: It can be source/destination
        """
        resource = self._get_resource()
        if hasattr(resource, type):
            for object in resource[type].iter():
                if object == value:
                    resource[type].remove(object)
        return self.client.put_resource(self.href, resource,
                                        EntityType.DEFAULT_CONTENT_TYPE.value)

    def list_firewall_rule_service(self):
        """Get the list of firewall rule's services.

        return: list of firewall rule's service details.
        e.g.
        [{'protocol': 'tcp', 'port': 200, 'sourcePort': 100},
         {'protocol': 'udp', 'port': 400, 'sourcePort': 300},
         {'protocol': 'icmp', 'icmpType': 'any'}]
        :rtype: list
        """
        resource = self._get_resource()
        firewall_rule_services = []
        if hasattr(resource, 'application'):
            if hasattr(resource.application, 'service'):
                for service in resource.application.service:
                    service_obj = {}
                    if hasattr(service, 'protocol'):
                        service_obj['Protocol'] = service.protocol
                    if hasattr(service, 'port'):
                        service_obj['Port'] = service.port
                    if hasattr(service, 'sourcePort'):
                        service_obj['Source port'] = service.sourcePort
                    if hasattr(service, 'icmpType'):
                        service_obj['Icmp type'] = service.icmpType
                    firewall_rule_services.append(service_obj)
        return firewall_rule_services

    def delete_firewall_rule_service(self, protocol):
        """Delete firewall rule's service from gateway.

        It will delete all services of given protocol.
        :param str protocol: protocol to remove services from application.
        """
        resource = self._get_resource()
        if hasattr(resource, 'application'):
            if hasattr(resource.application, 'service'):
                for service in resource.application.service:
                    if service.protocol == protocol:
                        resource.application.remove(service)
        return self.client.put_resource(self.href, resource,
                                        EntityType.DEFAULT_CONTENT_TYPE.value)
