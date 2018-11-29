# VMware vCloud Director Python SDK
# Copyright (c) 2014-2018 VMware, Inc. All Rights Reserved.
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
from pyvcloud.vcd.client import GatewayBackingConfigType
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.exceptions import AlreadyExistsException
from pyvcloud.vcd.exceptions import InvalidParameterException
from pyvcloud.vcd.utils import get_admin_href
from pyvcloud.vcd.platform import Platform


class Gateway(object):
    def __init__(self, client, name=None, href=None, resource=None):
        """Constructor for Gateway objects.

        :param pyvcloud.vcd.client.Client client: the client that will be used
            to make REST calls to vCD.
        :param str name: name of the entity.
        :param str href: URI of the entity.
        :param lxml.objectify.ObjectifiedElement resource: object containing
            EntityType.EDGE_GATEWAY XML data representing the gateway.
        """
        self.client = client
        self.name = name
        if href is None and resource is None:
            raise InvalidParameterException(
                "Gateway initialization failed as arguments are either "
                "invalid or None")
        self.href = href
        self.resource = resource
        if resource is not None:
            self.name = resource.get('name')
            self.href = resource.get('href')
        self.href_admin = get_admin_href(self.href)

    def get_resource(self):
        """Fetches the XML representation of the gateway from vCD.

        Will serve cached response if possible.

        :return: object containing EntityType.EDGE_GATEWAY XML data
        representing the gateway.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.reload()
        return self.resource

    def reload(self):
        """Reloads the resource representation of the gateway.

        This method should be called in between two method invocations on the
        Gateway object, if the former call changes the representation of the
        gateway in vCD.
        """
        self.resource = self.client.get_resource(self.href)
        if self.resource is not None:
            self.name = self.resource.get('name')
            self.href = self.resource.get('href')

    def convert_to_advanced(self):
        """Convert to advanced gateway.

        :return: object containing EntityType.TASK XML data representing the
            asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement

        """
        if self.resource is None:
            self.reload()

        return self.client.post_linked_resource(
            self.resource, RelationType.CONVERT_TO_ADVANCED_GATEWAY, None,
            None)

    def enable_distributed_routing(self, enable=True):
        """Enable Distributed Routing.

        :param bool enable: True if user want to enable else False.

        :return: object containing EntityType.TASK XML data
            representing the asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.reload()
        gateway = self.resource
        current_dr_status = gateway.Configuration.DistributedRoutingEnabled
        if enable == current_dr_status:
            return
        gateway.Configuration.DistributedRoutingEnabled = \
            E.DistributedRoutingEnabled(enable)
        return self.client.put_linked_resource(
            self.resource, RelationType.EDIT, EntityType.EDGE_GATEWAY.value,
            gateway)

    def modify_form_factor(self, gateway_type):
        """Modify form factor.

        This operation can be performed by only System Administrators.

        :param str gateway_type: gateway config type, possible values
            are compact/full/full4/x-large.

        :return: object containing EntityType.TASK XML data representing the
            asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: InvalidParameterException: if provided gateway config type
            is not from list compact/full/full4/x-large.
        """
        self.get_resource()
        try:
            GatewayBackingConfigType.__getitem__(gateway_type)
        except ValueError:
            raise InvalidParameterException(
                'Provided %s is not valid. It '
                'should be from allowed list '
                'compact/full/full4/x-large' % gateway_type)
        gateway_form_factor = E.EdgeGatewayFormFactor()
        gateway_form_factor.append(E.gatewayType(gateway_type))
        return self.client.post_linked_resource(
            self.resource, RelationType.MODIFY_FORM_FACTOR,
            EntityType.EDGE_GATEWAY_FORM_FACTOR.value, gateway_form_factor)

    def list_external_network_ip_allocations(self):
        """List external network ip allocations of the gateway.

        This operation can be performed by System/Org Administrators.

        :return: a dictionary that maps external network name to list of ip
            addresses. Ex: {'extnw1': ['10.10.10.2'...]}

        :rtype: dict
        """
        gateway = self.get_resource()
        out = {}
        for inf in gateway.Configuration.GatewayInterfaces.GatewayInterface:
            if inf.InterfaceType.text == 'uplink':
                ips = out.setdefault(inf.Name.text, [])
                ips.append(inf.SubnetParticipation.IpAddress.text)
        return out

    def redeploy(self):
        """Redeploy the gateway.

        :return: object containing EntityType.TASK XML data representing the
            asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.reload()

        return self.client.post_linked_resource(
            self.resource, RelationType.GATEWAY_REDEPLOY, None, None)

    def sync_syslog_settings(self):
        """Sync syslog settings of the gateway.

        :return: object containing EntityType.TASK XML data representing the
            asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.reload()

        return self.client.post_linked_resource(
            self.resource, RelationType.GATEWAY_SYNC_SYSLOG_SETTINGS, None,
            None)

    def _create_gateway_interafce(self, ext_nw, interface_type):
        """Creates gateway interface object connected to given network.

        :param lxml.objectify.ObjectifiedElement ext_nw: external network.

        :param str interface_type: interface type of the gateway.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        gateway_interface_param = E.GatewayInterface()
        gateway_interface_param.append(E.Name(ext_nw.get('name')))
        gateway_interface_param.append(E.DisplayName(ext_nw.get('name')))
        gateway_interface_param.append(E.Network(href=ext_nw.get('href')))
        gateway_interface_param.append(E.InterfaceType(interface_type))
        return gateway_interface_param

    def _get_external_network(self, name):
        """Gets external network object by given name.

        :param str name: external network name.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        platform = Platform(self.client)
        return platform.get_external_network(name)

    def add_external_network(self, network_name, ip_configuration):
        """Add the given external network to the gateway.

        :param str network_name: external network name.

        :param list ip_configuration: list of tuples that contain subnet in
            CIDR format and allocated ip address.
            Example [(10.10.10.1/24, Auto), (10.10.20.1/24, 10.10.20.3)]

        :return: object containing EntityType.TASK XML data representing the
            asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.reload()

        gateway = self.resource
        for inf in gateway.Configuration.GatewayInterfaces.GatewayInterface:
            if inf.Network.get('name') == network_name:
                raise AlreadyExistsException('External network ' +
                                             network_name +
                                             'already added to the gateway.')

        ext_nw = self._get_external_network(network_name)
        gw_interface = self._create_gateway_interafce(ext_nw, 'uplink')

        # Add subnet participation
        ip_scopes = ext_nw.xpath(
            'vcloud:Configuration/vcloud:IpScopes/vcloud:IpScope',
            namespaces=NSMAP)
        for ip_scope in ip_scopes:
            subnet_participation_param = E.SubnetParticipation()
            subnet = None
            for sn in ip_configuration:
                if sn[0].startswith(ip_scope.Gateway.text):
                    subnet = sn
                    break
            if subnet is None:
                continue

            ip_assigned = subnet[1].trim()
            # Configure Ip Settings
            subnet_participation_param.append(E.Gateway(ip_scope.Gateway.text))
            subnet_participation_param.append(E.Netmask(ip_scope.Netmask.text))
            subnet_participation_param.append(
                E.SubnetPrefixLength(ip_scope.SubnetPrefixLength.text))

            if not ip_assigned and ip_assigned != 'Auto':
                subnet_participation_param.append(E.IpAddress(ip_assigned))

            gw_interface.append(subnet_participation_param)

        gateway.Configuration.GatewayInterfaces.append(gw_interface)
        return self.client.put_linked_resource(
            self.resource, RelationType.GATEWAY_UPDATE_PROPERTIES,
            EntityType.EDGE_GATEWAY.value, gateway)

    def remove_external_network(self, network_name):
        """Remove the given external network to the gateway.

        :param str network_name: external network name.

        :return: object containing EntityType.TASK XML data representing the
            asynchronous task.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.resource is None:
            self.reload()

        gateway = self.resource
        interfaces = gateway.Configuration.GatewayInterfaces
        for inf in interfaces.GatewayInterface:
            if inf.Network.get('name') == network_name:
                interfaces.remove(inf)
                break
        return self.client.put_linked_resource(
            self.resource, RelationType.GATEWAY_UPDATE_PROPERTIES,
            EntityType.EDGE_GATEWAY.value, gateway)
