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
from pyvcloud.vcd.exceptions import EntityNotFoundException
from pyvcloud.vcd.exceptions import InvalidParameterException
from pyvcloud.vcd.vapp_services import VappServices


class VappStaticRoute(VappServices):
    def _makeStaticRouteServiceAttr(features):
        route_service = E.StaticRoutingService()
        route_service.append(E.IsEnabled(True))
        features.append(route_service)

    def enable_service(self, isEnable):
        """Enable static route service to vApp network.

        :param bool isEnable: True for enable and False for Disable.
        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is updating the vApp network.
        :rtype: lxml.objectify.ObjectifiedElement
        :raises: InvalidParameterException: Enable static route service failed
            as given network's connection is not routed
        """
        self._get_resource()
        fence_mode = self.resource.Configuration.FenceMode
        if fence_mode != 'natRouted':
            raise InvalidParameterException(
                "Enable static route service failed as given network's "
                "connection is not routed")
        features = self.resource.Configuration.Features
        if not hasattr(features, 'StaticRoutingService'):
            VappStaticRoute._makeStaticRouteServiceAttr(features)
        route = features.StaticRoutingService
        route.IsEnabled = E.IsEnabled(isEnable)
        return self.client.put_linked_resource(self.resource,
                                               RelationType.EDIT,
                                               EntityType.vApp_Network.value,
                                               self.resource)

    def add(self, name, network_cidr, next_hop_ip):
        """Add static route to vApp network.

        :param str name: name of route.
        :param str network_cidr: network CIDR.
        :param str next_hop_ip: next hop IP.
        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is updating the vApp network.
        :rtype: lxml.objectify.ObjectifiedElement
        :raises: InvalidParameterException: Add route to static route
            service failed as given network's connection is not routed
        """
        self._get_resource()
        fence_mode = self.resource.Configuration.FenceMode
        if fence_mode != 'natRouted':
            raise InvalidParameterException(
                "Add route to static route service failed as given network's "
                "connection is not routed")
        features = self.resource.Configuration.Features
        if not hasattr(features, 'StaticRoutingService'):
            VappStaticRoute._makeStaticRouteServiceAttr(features)
        route_service = features.StaticRoutingService
        static_route = E.StaticRoute()
        static_route.append(E.Name(name))
        static_route.append(E.Network(network_cidr))
        static_route.append(E.NextHopIp(next_hop_ip))
        route_service.append(static_route)
        return self.client.put_linked_resource(self.resource,
                                               RelationType.EDIT,
                                               EntityType.vApp_Network.value,
                                               self.resource)

    def list(self):
        """List static route of vApp network.

        :return: list of dictionary contain detail of static route.
        :rtype: list
        """
        list_of_route = []
        self._get_resource()
        fence_mode = self.resource.Configuration.FenceMode
        if fence_mode != 'natRouted':
            return list_of_route
        features = self.resource.Configuration.Features
        if not hasattr(features, 'StaticRoutingService'):
            return list_of_route
        route_service = features.StaticRoutingService
        for route in route_service.StaticRoute:
            result = {}
            result['Name'] = route.Name
            result['Network CIDR'] = route.Network
            result['Next Hop IP'] = route.NextHopIp
            list_of_route.append(result)
        return list_of_route

    def update(self, name, new_name=None, network_cidr=None, next_hop_ip=None):
        """Update static route to vApp network.

        :param str name: name of route.
        :param str new_name: new name of route.
        :param str network_cidr: network CIDR.
        :param str next_hop_ip: next hop IP.
        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is updating the vApp network.
        :rtype: lxml.objectify.ObjectifiedElement
        :raises: InvalidParameterException: Update route to static route
            service failed as given network's connection is not routed
        :raises: EntityNotFoundException: if the static route not exist of
            given name.
        """
        self._get_resource()
        fence_mode = self.resource.Configuration.FenceMode
        if fence_mode != 'natRouted':
            raise InvalidParameterException(
                "Update route to static route service failed as given "
                "network's connection is not routed")
        features = self.resource.Configuration.Features
        if not hasattr(features, 'StaticRoutingService'):
            raise EntityNotFoundException('static route ' + name +
                                          ' doesn\'t exist.')
        route_service = features.StaticRoutingService
        is_updated = False
        for route in route_service.StaticRoute:
            if route.Name == name:
                if new_name is not None:
                    route.Name = E.Name(new_name)
                if network_cidr is not None:
                    route.Network = E.Network(network_cidr)
                if next_hop_ip is not None:
                    route.NextHopIp = E.NextHopIp(next_hop_ip)
                is_updated = True
        if not is_updated:
            raise EntityNotFoundException('static route ' + name +
                                          ' doesn\'t exist.')
        else:
            return self.client.put_linked_resource(
                self.resource, RelationType.EDIT,
                EntityType.vApp_Network.value, self.resource)

    def delete(self, name):
        """Delete static route from vApp network.

        :param str name: name of static route.
        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is updating the vApp network.
        :rtype: lxml.objectify.ObjectifiedElement
        :raises: InvalidParameterException:  Delete route to static route
            service failed as given network's connection is not routed
        :raises: EntityNotFoundException: if the static route not exist of
            given name.
        """
        self._get_resource()
        fence_mode = self.resource.Configuration.FenceMode
        if fence_mode != 'natRouted':
            raise InvalidParameterException(
                "Delete route to static route service failed as given "
                "network's connection is not routed")
        features = self.resource.Configuration.Features
        if not hasattr(features, 'StaticRoutingService'):
            raise EntityNotFoundException('static route ' + name +
                                          ' doesn\'t exist.')
        route_service = features.StaticRoutingService
        is_deleted = False
        for route in route_service.StaticRoute:
            if route.Name == name:
                route_service.remove(route)
                is_deleted = True
        if not is_deleted:
            raise EntityNotFoundException('static route ' + name +
                                          ' doesn\'t exist.')
        else:
            return self.client.put_linked_resource(
                self.resource, RelationType.EDIT,
                EntityType.vApp_Network.value, self.resource)
