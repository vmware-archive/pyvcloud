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
from pyvcloud.vcd.network_url_constants import SERVICE_CERTIFICATE_POST


class Certificate(GatewayServices):

    def _reload(self):
        """Reloads the resource representation of the certificate."""
        self.resource = self.client.get_resource(self.href)

    def _build_self_href(self, resoure_id):
        network_url = self.network_url
        gateway_id = network_url.split("/")[-1]
        removal_string = '/edges/' + gateway_id
        network_url = network_url[:-len(removal_string)]
        certificate_href = \
            network_url + SERVICE_CERTIFICATE_POST + gateway_id + ':' \
            + resoure_id
        self.href = certificate_href

    def delete_certificate(self):
        """Delete certificate."""
        self.client.delete_resource(self.href)

    def delete_ca_certificate(self):
        self.delete_certificate()
