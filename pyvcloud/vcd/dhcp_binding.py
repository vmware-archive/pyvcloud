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
from pyvcloud.vcd.network_url_constants import DHCP_URL_TEMPLATE


class DhcpBinding(GatewayServices):

    def __init__(self, client, gateway_name=None, binding_id=None,
                 resource=None):
        super(DhcpBinding, self).__init__(client, gateway_name=gateway_name,
                                          resource_id=binding_id,
                                          resource=resource)

    def _build_self_href(self, binding_id):
        binding_href = (self.network_url + DHCP_URL_TEMPLATE)
        self.href = binding_href

    def __config_url(self):
        self._build_self_href(self.resource_id)
        return self.href

    def _reload(self):
        """Reloads the resource representation of the DHCP binding."""
        self.resource = self.client.get_resource(self.href)

    def delete_binding(self):
        """Delete a DHCP binding from gateway."""
        dhcp_resource = self._get_resource()
        if hasattr(dhcp_resource.staticBindings, 'staticBinding'):
            for static_binding in dhcp_resource.staticBindings.staticBinding:
                if static_binding.bindingId == self.resource_id:
                    dhcp_resource.staticBindings.remove(static_binding)
                    break

        self.client.put_resource(self.href, dhcp_resource,
                                 EntityType.DEFAULT_CONTENT_TYPE.value)
