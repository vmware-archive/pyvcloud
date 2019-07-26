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
from pyvcloud.vcd.exceptions import InvalidParameterException
from pyvcloud.vcd.vapp_services import VappServices


class VappFirewall(VappServices):
    def enable_firewall_service(self, isEnable):
        """Enable Firewall service to vApp network.

        :param bool isEnable: True for enable and False for Disable.
        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is updating the vApp network.
        :rtype: lxml.objectify.ObjectifiedElement
        :raises: InvalidParameterException: Enable firewall service failed as
            given network's connection is not routed
        """
        self._get_resource()
        fence_mode = self.resource.Configuration.FenceMode
        if fence_mode != 'natRouted':
            raise InvalidParameterException(
                "Enable firewall service failed as given network's connection "
                "is not routed")
        firewall = self.resource.Configuration.Features.FirewallService
        if isEnable:
            firewall.IsEnabled = E.IsEnabled(True)
        else:
            firewall.IsEnabled = E.IsEnabled(False)
        return self.client.put_linked_resource(
            self.resource, RelationType.EDIT, EntityType.vApp_Network.value,
            self.resource)

    def set_default_action(self, action='drop', log_action=True):
        """Set default action on firewall services to vApp network.

        :param string action: Default action on firewall service drop/allow.
        :param bool log_action: True for enable and False for Disable.
        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is updating the vApp network.
        :rtype: lxml.objectify.ObjectifiedElement
        :raises: InvalidParameterException: Enable firewall service failed as
            given network's connection is not routed
        """
        self._get_resource()
        fence_mode = self.resource.Configuration.FenceMode
        if fence_mode != 'natRouted':
            raise InvalidParameterException(
                "Enable firewall service failed as given network's connection "
                "is not routed")
        firewall_service = self.resource.Configuration.Features.FirewallService
        firewall_service.DefaultAction = E.DefaultAction(action)
        firewall_service.LogDefaultAction = E.LogDefaultAction(log_action)
        return self.client.put_linked_resource(
            self.resource, RelationType.EDIT, EntityType.vApp_Network.value,
            self.resource)

    def add_firewall_rule(self, name, is_enabled=False, policy='drop',
                          protocols=['Any'], source_port_range='Any',
                          source_ip='Any', destination_port_range='Any',
                          destination_ip='Any', enable_logging=False):
        """Add firewall rule on firewall services to vApp network.

        :param str name: name of firewall rule.
        :param str policy: policy on firewall rule.
        :param list protocols: list of protocols on firewall rule.
        :param str source_port_range: source port range for firewall rule.
        :param str source_ip: source IP.
        :param str destination_port_range:destination port range for firewall
            rule.
        :param str destination_ip: destination IP.
        :param str enable_logging: enable logging on firewall rule.
        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is updating the vApp network.
        :rtype: lxml.objectify.ObjectifiedElement
        :raises: InvalidParameterException: Enable firewall service failed as
            given network's connection is not routed
        """
        self._get_resource()
        fence_mode = self.resource.Configuration.FenceMode
        if fence_mode != 'natRouted':
            raise InvalidParameterException(
                "Enable firewall service failed as given network's connection "
                "is not routed")
        firewall_service = self.resource.Configuration.Features.FirewallService
        firewall_rule = E.FirewallRule()
        firewall_rule.append(E.IsEnabled(is_enabled))
        firewall_rule.append(E.Description(name))
        firewall_rule.append(E.Policy(policy))
        protocol = E.Protocols()
        for proto in protocols:
            if proto == 'Any':
                protocol.append(E.Any(True))
            elif proto == 'Icmp':
                protocol.append(E.Icmp(True))
            elif proto == 'Tcp':
                protocol.append(E.Tcp(True))
            elif proto == 'Udp':
                protocol.append(E.Udp(True))
        firewall_rule.append(protocol)
        firewall_rule.append(E.DestinationPortRange(destination_port_range))
        firewall_rule.append(E.DestinationIp(destination_ip))
        firewall_rule.append(E.SourcePortRange(source_port_range))
        firewall_rule.append(E.SourceIp(source_ip))
        firewall_rule.append(E.EnableLogging(enable_logging))
        firewall_service.append(firewall_rule)
        return self.client.put_linked_resource(self.resource,
                                               RelationType.EDIT,
                                               EntityType.vApp_Network.value,
                                               self.resource)

    def list_firewall_rule(self):
        """List all firewall rules on firewall services to vApp network.

        :return: a list of firewall rules info.
        :rtype: list
        :raises: InvalidParameterException: Enable firewall service failed as
            given network's connection is not routed
        """
        self._get_resource()
        fence_mode = self.resource.Configuration.FenceMode
        if fence_mode != 'natRouted':
            raise InvalidParameterException(
                "Enable firewall service failed as given network's connection "
                "is not routed")
        firewall_service = self.resource.Configuration.Features.FirewallService
        firewall_rule_list = []
        for firewall_rule in firewall_service.FirewallRule:
            info = {}
            info['Name'] = firewall_rule.Description
            info['Policy'] = firewall_rule.Policy
            info['IsEnabled'] = firewall_rule.IsEnabled
            info['DestinationPortRange'] = firewall_rule.DestinationPortRange
            info['DestinationIp'] = firewall_rule.DestinationIp
            info['SourcePortRange'] = firewall_rule.SourcePortRange
            info['SourceIp'] = firewall_rule.SourceIp
            info['EnableLogging'] = firewall_rule.EnableLogging
            list_of_protocol = []
            if hasattr(firewall_rule.Protocols, 'Any'):
                list_of_protocol.append('Any')
            if hasattr(firewall_rule.Protocols, 'Icmp'):
                list_of_protocol.append('Icmp')
            if hasattr(firewall_rule.Protocols, 'Tcp'):
                list_of_protocol.append('Tcp')
            if hasattr(firewall_rule.Protocols, 'Udp'):
                list_of_protocol.append('Udp')
            info['Protocols'] = ','.join(list_of_protocol)
            firewall_rule_list.append(info)
        return firewall_rule_list

    def update_firewall_rule(self, name, new_name=None, is_enabled=None,
                             policy=None, protocols=None,
                             source_port_range=None,
                             source_ip=None, destination_port_range=None,
                             destination_ip=None, enable_logging=None):
        """Update firewall rule on firewall services to vApp network.

        :param str name: name of firewall rule.
        :param str new_name: new name of firewall rule.
        :param str policy: policy on firewall rule.
        :param list protocols: list of protocols on firewall rule.
        :param str source_port_range: source port range for firewall rule.
        :param str source_ip: source IP.
        :param str destination_port_range:destination port range for firewall
            rule.
        :param str destination_ip: destination IP.
        :param str enable_logging: enable logging on firewall rule.
        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is updating the vApp network.
        :rtype: lxml.objectify.ObjectifiedElement
        :raises: InvalidParameterException: Enable firewall service failed as
            given network's connection is not routed
        """
        self._get_resource()
        fence_mode = self.resource.Configuration.FenceMode
        if fence_mode != 'natRouted':
            raise InvalidParameterException(
                "Enable firewall service failed as given network's connection "
                "is not routed")
        firewall_service = self.resource.Configuration.Features.FirewallService
        for firewall_rule in firewall_service.FirewallRule:
            if firewall_rule.Description == name:
                if new_name is not None:
                    firewall_rule.Description = E.Description(new_name)
                if is_enabled is not None:
                    firewall_rule.IsEnabled = E.IsEnabled(is_enabled)
                if policy is not None:
                    firewall_rule.Policy = E.Policy(policy)
                if protocols is not None:
                    protocol = E.Protocols()
                    for proto in protocols:
                        if proto == 'Any':
                            protocol.append(E.Any(True))
                        elif proto == 'Icmp':
                            protocol.append(E.Icmp(True))
                        elif proto == 'Tcp':
                            protocol.append(E.Tcp(True))
                        elif proto == 'Udp':
                            protocol.append(E.Udp(True))
                    firewall_rule.Protocols = protocol
                if destination_port_range is not None:
                    firewall_rule.DestinationPortRange = \
                        E.DestinationPortRange(destination_port_range)
                if destination_ip is not None:
                    firewall_rule.DestinationIp = E.DestinationIp(
                        destination_ip)
                if source_port_range is not None:
                    firewall_rule.SourcePortRange = E.SourcePortRange(
                        source_port_range)
                if source_ip is not None:
                    firewall_rule.SourceIp = E.SourceIp(source_ip)
                if enable_logging is not None:
                    firewall_rule.EnableLogging = E.EnableLogging(
                        enable_logging)
        return self.client.put_linked_resource(self.resource,
                                               RelationType.EDIT,
                                               EntityType.vApp_Network.value,
                                               self.resource)

    def delete_firewall_rule(self, name):
        """Delete firewall rule on firewall services to vApp network.

        :param str name: name of firewall rule.
        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is updating the vApp network.
        :rtype: lxml.objectify.ObjectifiedElement
        :raises: InvalidParameterException: Enable firewall service failed as
            given network's connection is not routed
        """
        self._get_resource()
        fence_mode = self.resource.Configuration.FenceMode
        if fence_mode != 'natRouted':
            raise InvalidParameterException(
                "Enable firewall service failed as given network's connection "
                "is not routed")
        firewall_service = self.resource.Configuration.Features.FirewallService
        for firewall_rule in firewall_service.FirewallRule:
            if firewall_rule.Description == name:
                firewall_service.remove(firewall_rule)
        return self.client.put_linked_resource(self.resource,
                                               RelationType.EDIT,
                                               EntityType.vApp_Network.value,
                                               self.resource)
