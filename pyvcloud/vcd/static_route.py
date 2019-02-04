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

from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.gateway_services import GatewayServices
from pyvcloud.vcd.network_url_constants import STATIC_ROUTE_URL_TEMPLATE


class StaticRoute(GatewayServices):
    """This class will be used to configure static routes on gateway."""

    def __init__(self, client, gateway_name=None, route_network_id=None,
                 route_resource=None, href=None):
        super(StaticRoute, self).__init__(client, gateway_name=gateway_name,
                                          resource_id=route_network_id,
                                          resource=route_resource,
                                          resource_href=href)

    def _build_self_href(self, network):
        static_route_href = (self.network_url + STATIC_ROUTE_URL_TEMPLATE)
        self.href = static_route_href

    def _reload(self):
        """Reloads the resource representation of static route."""
        self.resource = self.client.get_resource(self.href)

    def delete_static_route(self):
        """Delete a static route from gateway."""
        static_resource = self._get_resource()
        for static_route in static_resource.staticRoutes.route:
            if static_route.network == self.resource_id:
                static_resource.staticRoutes.remove(static_route)
        self.client.put_resource(self.href, static_resource,
                                 EntityType.DEFAULT_CONTENT_TYPE.value)
