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
from pyvcloud.vcd.gateway_services import GatewayServices
from pyvcloud.vcd.network_url_constants import FIREWALL_RULE_URL_TEMPLATE
from pyvcloud.vcd.network_url_constants import FIREWALL_RULES_URL_TEMPLATE
from pyvcloud.vcd.network_url_constants import FIREWALL_URL_TEMPLATE


class FirewallRule(GatewayServices):

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
