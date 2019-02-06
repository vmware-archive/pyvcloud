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
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.exceptions import EntityNotFoundException
from pyvcloud.vcd.gateway_services import GatewayServices
from pyvcloud.vcd.network_url_constants import IPSEC_VPN_URL_TEMPLATE


class IpsecVpn(GatewayServices):

    def __init__(self, client, gateway_name=None, ipsec_end_point=None):
        """Constructor for IPsec VPN objects.

        :param pyvcloud.vcd.client.Client client: the client that will be used
            to make REST calls to vCD.
        :param str gateway_name: name of the gateway entity.
        :param str ipsec_end_point: local_end_point-peer_end_point.
        It is a unique string to identify a ipsec vpn.
        :param lxml.objectify.ObjectifiedElement resource: object containing
            EntityType.IPSEC_VPN XML data representing the ipsec vpn rule.
        """
        super(IpsecVpn, self).__init__(client, gateway_name=gateway_name,
                                       resource_id=ipsec_end_point)
        self.end_point = ipsec_end_point
        self.resource = self.get_ipsec_config_resource()

    def reload(self):
        """Reloads the resource representation of the ipsec vpn."""
        self.resource = self.client.get_resource(self.href)

    # NOQA
    def _build_self_href(self, resoure_id):
        ipsec_vpn_href = (self.network_url + IPSEC_VPN_URL_TEMPLATE)
        self.href = ipsec_vpn_href

    def get_ipsec_config_resource(self):
        return self.client.get_resource(self.href)

    def set_log_level(self, log_level):
        """Set log level for Ipsec VPN.

        :param str log_level: log level
        """
        log_level_set = set(
            ["emergency", "alert", "critical", "error", "warning",
             "notice", "info", "debug"])
        if log_level not in log_level_set:
            raise EntityNotFoundException('No associated log level found.')

        ipsec_vpn = self.resource
        ipsec_vpn.logging.logLevel = log_level
        self.client.put_resource(self.href,
                                 ipsec_vpn,
                                 EntityType.DEFAULT_CONTENT_TYPE.value)

    def info_logging_settings(self):
        """Provide info for logging settings.

        :return: dict: dict of info of logging settings
        """
        ipsec_logging_settings = {}
        ipsec_vpn = self.resource
        ipsec_logging_settings["Enable"] = \
            ipsec_vpn.logging.enable.text
        ipsec_logging_settings["Log Level"] = \
            ipsec_vpn.logging.logLevel

        return ipsec_logging_settings

    def list_ipsec_vpn(self):
        """List IPsec VPN of a gateway.

        :return: list of all ipsec vpn.
        """
        out_list = []
        ipsec_vpn = self.resource
        vpn_sites = ipsec_vpn.sites
        if hasattr(vpn_sites, "site"):
            for site in vpn_sites.site:
                ipsec_vpn_info = {}
                ipsec_vpn_info["Name"] = site.name
                ipsec_vpn_info["local_ip"] = site.localIp
                ipsec_vpn_info["peer_ip"] = site.peerIp
                out_list.append(ipsec_vpn_info)
        return out_list

    def delete_ipsec_vpn(self):
        """Delete IP sec Vpn."""
        end_points = self.end_point.split('-')
        local_ip = end_points[0]
        peer_ip = end_points[1]
        ipsec_vpn = self.resource
        vpn_sites = ipsec_vpn.sites
        for site in vpn_sites.site:
            if site.localIp == local_ip and site.peerIp == peer_ip:
                vpn_sites.remove(site)

        self.client.put_resource(self.href,
                                 ipsec_vpn,
                                 EntityType.DEFAULT_CONTENT_TYPE.value)

    def enable_activation_status(self, is_active):
        """Enables activation status of IPsec VPN.

        :param bool is_active: flag to enable/disable activation status
        """
        ipsec_vpn = self.resource
        ipsec_vpn.enabled = is_active
        self.client.put_resource(self.href,
                                 ipsec_vpn,
                                 EntityType.DEFAULT_CONTENT_TYPE.value)

    def info_activation_status(self):
        """Info activation status.

        :return: dict activation status dict
        """
        ipsec_vpn_activation_status = {}
        ipsec_vpn = self.resource
        ipsec_vpn_activation_status["Activation Status"] = \
            ipsec_vpn.enabled.text
        return ipsec_vpn_activation_status

    def change_shared_key(self, shared_key):
        """Changes shared key.

        :param str shared_key: shared key.
        """
        ipsec_vpn = self.resource
        ip_sec_global = ipsec_vpn.xpath('global', namespaces=NSMAP)
        ip_sec_global[0].psk = shared_key

        self.client.put_resource(self.href,
                                 ipsec_vpn,
                                 EntityType.DEFAULT_CONTENT_TYPE.value)

    def enable_logging(self, is_enable):
        """Enables logging for IPsec VPN.

        :param bool is_enable: flag to enable/disable logging.
        """
        ipsec_vpn = self.resource
        ipsec_vpn.logging.enable = is_enable
        self.client.put_resource(self.href,
                                 ipsec_vpn,
                                 EntityType.DEFAULT_CONTENT_TYPE.value)
