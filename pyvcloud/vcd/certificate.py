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

    def __init__(self, client, gateway_name=None, certificate_object_id=None):
        """Constructor for Certificate objects.

        :param pyvcloud.vcd.client.Client client: the client that will be used
            to make REST calls to vCD.
        :param str gateway_name: name of the gateway entity.
        :param str certificate_object_id: certificate object id.
            EntityType.certificate XML data representing the certificate.
        """
        super(Certificate, self).__init__(client, gateway_name=gateway_name,
                                          resource_id=certificate_object_id)
        self.object_id = certificate_object_id
        self.resource = self.get_certificate_resource()

    def reload(self):
        """Reloads the resource representation of the ipsec vpn."""
        self.resource = self.client.get_resource(self.href)

    # NOQA
    def _build_self_href(self, resoure_id):
        network_url = self.network_url
        gateway_id = network_url.split("/")[-1]
        removal_string = '/edges/' + gateway_id
        network_url = network_url[:-len(removal_string)]
        certificate_href = \
            network_url + SERVICE_CERTIFICATE_POST + gateway_id + ':' \
            + resoure_id
        self.href = certificate_href

    def get_certificate_resource(self):
        return self.client.get_resource(self.href)

    def delete_certificate(self):
        """Delete certificate."""
        self.client.delete_resource(self.href)

    def delete_ca_certificate(self):
        self.delete_certificate()
