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
                break

        self.client.put_resource(self.href,
                                 ipsec_vpn,
                                 EntityType.DEFAULT_CONTENT_TYPE.value)

    def update_ipsec_vpn(self,
                         name=None,
                         peer_id=None,
                         peer_ip_address=None,
                         local_id=None,
                         local_ip_address=None,
                         local_subnet=None,
                         peer_subnet=None,
                         shared_secret_encrypted=None,
                         encryption_protocol=None,
                         authentication_mode=None,
                         dh_group=None,
                         description=None,
                         mtu=None,
                         is_enabled=None,
                         enable_pfs=None):
        """Update IPsec VPN of the gateway.

        param str name: new name of IPSec VPN
        param str description: new description of IPSec VPN
        param str peer_id: new peer id
        param str peer_ip_address: new peer IP address
        param str local_id: new local id
        param str local_ip_address: new local IP address
        param str local_subnet: new local subnet in CIDR format
        param str peer_subnet: new peer subnet in CIDR format
        param str shared_secret_encrypted: new shared secret encrypted
        param str encryption_protocol: new encryption protocol
        param str authentication_mode: new authentication mode
        param str dh_group: new dh group
        param str mtu: new MTU
        param bool is_enabled: new enabled status Default : false
        param bool enable_pfs: new enabled pfs status Default : false
        :return: Ipsec Vpn object
        :rtype: lxml.objectify.ObjectifiedElement
        """
        end_points = self.end_point.split('-')
        local_ip = end_points[0]
        peer_ip = end_points[1]
        ipsec_vpn = self.resource
        vpn_sites = ipsec_vpn.sites
        for site in vpn_sites.site:
            if site.localIp == local_ip and site.peerIp == peer_ip:
                if is_enabled is not None:
                    site.enabled = E.enabled(is_enabled)
                if name is not None:
                    site.name = E.name(name)
                if description is not None:
                    site.description = E.description(description)
                if local_id is not None:
                    site.localId = E.localId(local_id)
                if local_ip_address is not None:
                    site.localIp = E.localIp(local_ip_address)
                if peer_id is not None:
                    site.peerId = E.peerId(peer_id)
                if peer_ip_address is not None:
                    site.peerIp = E.peerIp(peer_ip_address)
                if encryption_protocol is not None:
                    site.encryptionAlgorithm = \
                        E.encryptionAlgorithm(encryption_protocol)
                if mtu is not None:
                    site.mtu = E.mtu(mtu)
                if enable_pfs is not None:
                    site.enablePfs = E.enablePfs(enable_pfs)
                if local_subnet is not None:
                    local_subnets = E.localSubnets()
                    if ',' in local_subnet:
                        subnet_list = local_subnet.split(",")
                        for subnet in subnet_list:
                            local_subnets.append(E.subnet(subnet))
                    else:
                        local_subnets.append(E.subnet(local_subnet))
                    site.localSubnets = local_subnets
                if peer_subnet is not None:
                    peer_subnets = E.peerSubnets()
                    if ',' in peer_subnet:
                        subnet_list = peer_subnet.split(",")
                        for subnet in subnet_list:
                            peer_subnets.append(E.subnet(subnet))
                    else:
                        peer_subnets.append(E.subnet(peer_subnet))
                    site.peerSubnets = peer_subnets
                if shared_secret_encrypted is not None:
                    site.psk = E.psk(shared_secret_encrypted)
                if authentication_mode is not None:
                    site.authenticationMode = \
                        E.authenticationMode(authentication_mode)
                if dh_group is not None:
                    site.dhGroup = E.dhGroup(dh_group)
                break

        self.client.put_resource(self.href, ipsec_vpn,
                                 EntityType.DEFAULT_CONTENT_TYPE.value)

    def get_vpn_site_info(self):
        """Get the details of Ipsec VPN site.

        :return: Dictionary having nat rule details.

        :rtype: Dictionary
        """
        vpn_site_info = {}
        end_points = self.end_point.split('-')
        local_ip = end_points[0]
        peer_ip = end_points[1]
        ipsec_vpn = self.resource
        vpn_sites = ipsec_vpn.sites
        for site in vpn_sites.site:
            if site.localIp == local_ip and site.peerIp == peer_ip:
                vpn_site_info['Name'] = site.name
                vpn_site_info['description'] = site.description
                vpn_site_info['localId'] = site.localId
                vpn_site_info['localIp'] = site.localIp
                vpn_site_info['peerId'] = site.peerId
                vpn_site_info['peerIp'] = site.peerIp
                localsubnets = ''
                for subnet in site.localSubnets.subnet:
                    localsubnets = localsubnets + subnet + '-'
                localsubnets = localsubnets[:-1]
                vpn_site_info['localSubnets'] = localsubnets
                peersubnets = ''
                for subnet in site.peerSubnets.subnet:
                    peersubnets = peersubnets + subnet + '-'
                peersubnets = peersubnets[:-1]
                vpn_site_info['peerSubnets'] = peersubnets
                vpn_site_info['enabled'] = site.enabled
                vpn_site_info['encryptionAlgorithm'] = site.encryptionAlgorithm
                vpn_site_info['mtu'] = site.mtu
                vpn_site_info['enablePfs'] = site.enablePfs
                vpn_site_info['dhGroup'] = site.dhGroup
                break

        return vpn_site_info
