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
from pyvcloud.vcd.client import E
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.exceptions import InvalidParameterException
from pyvcloud.vcd.platform import Platform
from pyvcloud.vcd.utils import get_admin_href


class ExternalNetwork(object):
    def __init__(self, client, name=None, href=None, resource=None):
        """Constructor for External Network objects.

        :param pyvcloud.vcd.client.Client client: the client that will be used
            to make REST calls to vCD.
        :param str name: name of the entity.
        :param str href: URI of the entity.
        :param lxml.objectify.ObjectifiedElement resource: object containing
            EntityType.EXTERNAL_NETWORK XML data representing the external
            network.
        """
        self.client = client
        self.name = name
        if href is None and resource is None:
            raise InvalidParameterException(
                "External network initialization failed as arguments are "
                "either invalid or None")
        self.href = href
        self.resource = resource
        if resource is not None:
            self.name = resource.get('name')
            self.href = resource.get('href')
        self.href_admin = get_admin_href(self.href)

    def get_resource(self):
        """Fetches the XML representation of the external network from vCD.

        Will serve cached response if possible.

        :return: object containing EntityType.EXTERNAL_NETWORK XML data
        representing the external network.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.reload()
        return self.resource

    def reload(self):
        """Reloads the resource representation of the external network.

        This method should be called in between two method invocations on the
        external network object, if the former call changes the representation
        of the external network in vCD.
        """
        self.resource = self.client.get_resource(self.href)
        if self.resource is not None:
            self.name = self.resource.get('name')
            self.href = self.resource.get('href')

    def add_subnet(self,
                   name,
                   gateway_ip,
                   netmask,
                   ip_ranges,
                   primary_dns_ip=None,
                   secondary_dns_ip=None,
                   dns_suffix=None):
        """Add subnet to an external network.

        :param str name: Name of external network.

        :param str gateway_ip: IP address of the gateway of the new network.

        :param str netmask: Netmask of the gateway.

        :param list ip_ranges: list of IP ranges used for static pool
            allocation in the network. For example, [192.168.1.2-192.168.1.49,
            192.168.1.100-192.168.1.149].

        :param str primary_dns_ip: IP address of primary DNS server.

        :param str secondary_dns_ip: IP address of secondary DNS Server.

        :param str dns_suffix: DNS suffix.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.reload()

        platform = Platform(self.client)
        ext_net = platform.get_external_network(name)
        config = ext_net['{' + NSMAP['vcloud'] + '}Configuration']
        ip_scopes = config.IpScopes

        ip_scope = E.IpScope()
        ip_scope.append(E.IsInherited(False))
        ip_scope.append(E.Gateway(gateway_ip))
        ip_scope.append(E.Netmask(netmask))
        if primary_dns_ip is not None:
            ip_scope.append(E.Dns1(primary_dns_ip))
        if secondary_dns_ip is not None:
            ip_scope.append(E.Dns2(secondary_dns_ip))
        if dns_suffix is not None:
            ip_scope.append(E.DnsSuffix(dns_suffix))
        e_ip_ranges = E.IpRanges()
        for ip_range in ip_ranges:
            e_ip_range = E.IpRange()
            ip_range_token = ip_range.split('-')
            e_ip_range.append(E.StartAddress(ip_range_token[0]))
            e_ip_range.append(E.EndAddress(ip_range_token[1]))
            e_ip_ranges.append(e_ip_range)
        ip_scope.append(e_ip_ranges)
        ip_scopes.append(ip_scope)

        return self.client.put_linked_resource(
            ext_net,
            rel=RelationType.EDIT,
            media_type=EntityType.EXTERNAL_NETWORK.value,
            contents=ext_net)

    def enable_subnet(self, gateway_ip, is_enabled=None):
        """Enable subnet of an external network.

        :param str gateway_ip: IP address of the gateway of external network.

        :param bool is_enabled: flag to enable/disable the subnet

        :rtype: lxml.objectify.ObjectifiedElement
        """
        ext_net = self.client.get_resource(self.href)

        config = ext_net['{' + NSMAP['vcloud'] + '}Configuration']
        ip_scopes = config.IpScopes

        if is_enabled is not None:
            for ip_scope in ip_scopes.IpScope:
                if ip_scope.Gateway == gateway_ip:
                    if hasattr(ip_scope, 'IsEnabled'):
                        ip_scope['IsEnabled'] = E.IsEnabled(is_enabled)
                        return self.client. \
                            put_linked_resource(ext_net, rel=RelationType.EDIT,
                                                media_type=EntityType.
                                                EXTERNAL_NETWORK.value,
                                                contents=ext_net)
        return ext_net

    def add_ip_range(self, gateway_ip, ip_ranges):
        """Enable subnet of an external network.

        :param str gateway_ip: IP address of the gateway of external network.

        :param list ip_ranges: list of IP ranges used for static pool
            allocation in the network. For example, [192.168.1.2-192.168.1.49,
            192.168.1.100-192.168.1.149]

        :rtype: lxml.objectify.ObjectifiedElement
        """
        ext_net = self.client.get_resource(self.href)

        config = ext_net['{' + NSMAP['vcloud'] + '}Configuration']
        ip_scopes = config.IpScopes

        for ip_scope in ip_scopes.IpScope:
            if ip_scope.Gateway == gateway_ip:
                existing_ip_ranges = ip_scope.IpRanges
                all_ranges = ip_ranges.split(',')
                for range in all_ranges:
                    range_token = range.split('-')
                    e_ip_range = E.IpRange()
                    e_ip_range.append(E.StartAddress(range_token[0]))
                    e_ip_range.append(E.EndAddress(range_token[1]))
                    existing_ip_ranges.append(e_ip_range)

        return self.client. \
            put_linked_resource(ext_net, rel=RelationType.EDIT,
                                media_type=EntityType.
                                EXTERNAL_NETWORK.value,
                                contents=ext_net)
        return ext_net
