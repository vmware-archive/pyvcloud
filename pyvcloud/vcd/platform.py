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

import urllib.parse
import uuid

from pyvcloud.vcd.client import E
from pyvcloud.vcd.client import E_VMEXT
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import QueryResultFormat
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.extension import Extension


class Platform(object):
    """Helper class to interact with vSphere Platform resources.

    Attributes:
        client (str): Low level client to connect to vCD.
        extension (:obj:`pyvcloud.vcd.Extension`, optional): It holds an
            Extension object to interact with vCD admin extension.

    """

    def __init__(self, client):
        """Constructor for vSphere Platform Resources.

        :param client:  (pyvcloud.vcd.client): The client.
        """
        self.client = client
        self.extension = Extension(client)

    def list_vcenters(self):
        """List vCenter servers attached to the system.

        :return: (lxml.objectify.ObjectifiedElement): list of vCenter
            references.
        """
        return self.client.get_linked_resource(
            self.extension.get_resource(), RelationType.DOWN,
            EntityType.VIM_SERVER_REFS.value).VimServerReference

    def get_vcenter(self, name):
        """Get a vCenter attached to the system by name.

        :param name: (str): The name of vCenter.

        :return: (lxml.objectify.ObjectifiedElement): vCenter resource.

        :raises: Exception: If the named vCenter cannot be located.
        """
        for record in self.list_vcenters():
            if record.get('name') == name:
                return self.client.get_resource(record.get('href'))
        raise Exception('vCenter \'%s\' not found' % name)

    def list_external_networks(self):
        """List all external networks available in the system.

        :return:  A list of :class:`lxml.objectify.StringElement` objects
            representing the external network references.
        """
        ext_net_refs = self.client.get_linked_resource(
            self.extension.get_resource(), RelationType.DOWN,
            EntityType.EXTERNAL_NETWORK_REFS.value)

        if hasattr(ext_net_refs, 'ExternalNetworkReference'):
            return ext_net_refs.ExternalNetworkReference

        return []

    def get_external_network(self, name):
        """Fetch an external network resource identified by it's name.

        :param name: (str): The name of the external network.

        :return: A :class:`lxml.objectify.StringElement` object representing
            the reference to external network.

        :raises: Exception: If the named external network cannot be located.
        """
        ext_net_refs = self.list_external_networks()
        for ext_net in ext_net_refs:
            if ext_net.get('name') == name:
                return self.client.get_resource(ext_net.get('href'))
        raise Exception('External network \'%s\' not found.' % name)

    def get_vxlan_network_pool(self, vxlan_network_pool_name):
        """Fetch a vxlan_networ_pool by its name.

        :param: vxlan_network_pool_name (str): name of the vxlan_network_pool.
        :return: (lxml.objectify.ObjectifiedElement): vxlan_network_pool.
        :raises: Exception: If the named vxlan_network_pool cannot be found.
        """
        query_filter = 'name==%s' % urllib.parse.quote_plus(
            vxlan_network_pool_name)
        query = self.client.get_typed_query(
            'networkPool',
            query_result_format=QueryResultFormat.RECORDS,
            qfilter=query_filter)
        records = list(query.execute())
        vxlan_network_pool_record = None
        for record in records:
            if vxlan_network_pool_name == record.get('name'):
                vxlan_network_pool_record = record
                break
        if vxlan_network_pool_record is not None:
            return vxlan_network_pool_record
        raise Exception('vxlan_network_pool \'%s\' not found' %
                        vxlan_network_pool_name)

    def get_resource_pool_morefs(self, vc_name, vc_href, resource_pool_names):
        """Fetch list of morefs for a given list of resource_pool_names.

        :param: vc_name (str): vim_server name.
        :param: vc_href (href): vim_server href.
        :param: resource_pool_names (list): list of resource_pool_names.
        :return: list of morefs corresponding to resource_pool_names.
        :raises: Exception: if any resource_pool_name cannot be found.
        """
        morefs = []
        resource_pool_list = self.client.get_resource(vc_href +
                                                      '/resourcePoolList')
        if hasattr(resource_pool_list, 'ResourcePool'):
            for resource_pool_name in resource_pool_names:
                res_pool_found = False
                for resource_pool in resource_pool_list.ResourcePool:
                    if resource_pool.DataStoreRefs.VimObjectRef.VimServerRef.\
                       get('name') == vc_name:  # rp belongs to VC
                        name = resource_pool.get('name')
                        moref = resource_pool.MoRef.text
                        if name == resource_pool_name:
                            morefs.append(moref)
                            res_pool_found = True
                            break
                if not res_pool_found:
                    raise Exception('resource pool \'%s\' not Found' %
                                    resource_pool_name)
        return morefs

    def create_provider_vdc(self,
                            vim_server_name,
                            resource_pool_names,
                            storage_profiles,
                            pvdc_name,
                            is_enabled=None,
                            description=None,
                            highest_hw_vers=None,
                            vxlan_network_pool=None):
        """Create a Provider Virtual Datacenter.

        :param: vim_server_name: (str): vim_server_name (VC name).
        :param: resource_pool_names: (list): list of resource_pool_names.
        :param: storage_profiles: (list): list of storageProfile namespace.
        :param: pvdc_name: (str): name of PVDC to be created.
        :param: is_enabled: (boolean): enable flag.
        :param: description: (str): description of pvdc.
        :param: highest_hw_vers: (str): highest supported hw vers number.
        :param: vxlan_network_pool: (str): name of vxlan_network_pool.
        :return: A :class:lxml.objectify.StringElement object describing the
        :        new provider VDC.
        """
        vc_record = self.get_vcenter(vim_server_name)
        vc_href = vc_record.get('href')
        rp_morefs = self.get_resource_pool_morefs(vim_server_name,
                                                  vc_href,
                                                  resource_pool_names)
        vmw_prov_vdc_params = E_VMEXT.VMWProviderVdcParams(name=pvdc_name)
        if description is not None:
            vmw_prov_vdc_params.append(E.Description(description))
        resource_pool_refs = E_VMEXT.ResourcePoolRefs()
        for rp_moref in rp_morefs:
            vim_object_ref = E_VMEXT.VimObjectRef()
            vim_object_ref.append(E_VMEXT.VimServerRef(href=vc_href))
            vim_object_ref.append(E_VMEXT.MoRef(rp_moref))
            vim_object_ref.append(E_VMEXT.VimObjectType('RESOURCE_POOL'))
            resource_pool_refs.append(vim_object_ref)
        vmw_prov_vdc_params.append(resource_pool_refs)
        vmw_prov_vdc_params.append(E_VMEXT.VimServer(href=vc_href))
        if vxlan_network_pool is not None:
            vxlan_network_pool_record = self.get_vxlan_network_pool(
                vxlan_network_pool)
            vx_href = vxlan_network_pool_record.get('href')
            vmw_prov_vdc_params.append(E_VMEXT.VxlanNetworkPool(
                href=vx_href))
        if highest_hw_vers is not None:
            vmw_prov_vdc_params.append(
                E_VMEXT.HighestSupportedHardwareVersion(highest_hw_vers))
        if is_enabled is not None:
            vmw_prov_vdc_params.append(E_VMEXT.IsEnabled(is_enabled))
        for storage_profile in storage_profiles:
            vmw_prov_vdc_params.append(E_VMEXT.StorageProfile(
                storage_profile))
        random_username_suffix = uuid.uuid4().hex
        default_user = 'USR' + random_username_suffix[:8]
        default_pwd = 'PWD' + random_username_suffix[:8]
        vmw_prov_vdc_params.append(E_VMEXT.DefaultPassword(default_pwd))
        vmw_prov_vdc_params.append(E_VMEXT.DefaultUsername(default_user))

        return self.client.post_linked_resource(self.extension.get_resource(),
                                                rel=RelationType.ADD,
                                                media_type=EntityType.
                                                PROVIDER_VDC_PARAMS.value,
                                                contents=vmw_prov_vdc_params)

    def attach_vcenter(self,
                       vc_server_name,
                       vc_server_host,
                       vc_admin_user,
                       vc_admin_pwd,
                       nsx_server_name=None,
                       nsx_host=None,
                       nsx_admin_user=None,
                       nsx_admin_pwd=None,
                       is_enabled=None):
        """Register (attach) a VirtualCenter server (also known as VimServer).

        :param: vc_server_name: (str): vc_server_name (VC name).
        :param: vc_server_host: (str): FQDN or IP address of VC host.
        :param: vc_admin_user: (str): vc_admin user.
        :param: vc_admin_pwd: (str): vc_admin password.
        :param: nsx_server_name: (str): NSX server name.
        :param: nsx_host (str): FQDN or IP address of NSX host.
        :param: nsx_admin_user: (str): NSX admin user.
        :param: nsx_admin_pwd: (str): NSX admin password.
        :return: A :class:lxml.objectify.StringElement object describing the
        :        newly registered (attached) VimServer.
        """
        register_vc_server_params = E_VMEXT.RegisterVimServerParams()
        vc_server = E_VMEXT.VimServer(name=vc_server_name)
        vc_server.append(E_VMEXT.Username(vc_admin_user))
        vc_server.append(E_VMEXT.Password(vc_admin_pwd))
        vc_server.append(E_VMEXT.Url('https://' + vc_server_host + ':443'))
        if is_enabled is not None:
            vc_server.append(E_VMEXT.IsEnabled(is_enabled))
        register_vc_server_params.append(vc_server)
        if nsx_server_name is not None:
            nsx_manager = E_VMEXT.ShieldManager(name=nsx_server_name)
            nsx_manager.append(E_VMEXT.Username(nsx_admin_user))
            nsx_manager.append(E_VMEXT.Password(nsx_admin_pwd))
            nsx_manager.append(E_VMEXT.Url('https://' + nsx_host + ':443'))
            register_vc_server_params.append(nsx_manager)

        return self.client.\
            post_linked_resource(resource=self.extension.get_resource(),
                                 rel=RelationType.ADD,
                                 media_type=EntityType.
                                 REGISTER_VC_SERVER_PARAMS.value,
                                 contents=register_vc_server_params)
