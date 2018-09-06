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

import uuid

from pyvcloud.vcd.client import E
from pyvcloud.vcd.client import E_VMEXT
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import get_links
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import QueryResultFormat
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.client import ResourceType
from pyvcloud.vcd.exceptions import EntityNotFoundException
from pyvcloud.vcd.exceptions import InvalidStateException
from pyvcloud.vcd.exceptions import ValidationError
from pyvcloud.vcd.extension import Extension
from pyvcloud.vcd.utils import get_admin_extension_href


class Platform(object):
    """Helper class to interact with vSphere Platform resources.

    Attributes:
        - client (pyvcloud.vcd.client): Low level client to connect to vCD.
        - extension (:obj:`pyvcloud.vcd.Extension`, optional): It holds an
            Extension object to interact with vCD admin extension.

    """

    def __init__(self, client):
        """Constructor for Platform object.

        :param pyvcloud.vcd.client.Client client: the client that will be used
            to make REST calls to vCD.
        """
        self.client = client
        self.extension = Extension(client)

    def list_vcenters(self):
        """List vCenter servers attached to the system.

        :return: list of object containing vmext:VimServerReference XML element
            that represent vCenter references.

        :rtype: list
        """
        vim_server_references = self.client.get_linked_resource(
            self.extension.get_resource(),
            RelationType.DOWN,
            EntityType.VIM_SERVER_REFS.value)
        if hasattr(vim_server_references, 'VimServerReference'):
            return vim_server_references.VimServerReference
        else:
            return []

    def get_vcenter(self, name):
        """Fetch a vCenter attached to the system by name.

        :param str name: name of vCenter.

        :return: an object containing EntityType.VIRTUAL_CENTER XML data which
            represents a vCenter server.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: EntityNotFoundException: if the named vCenter cannot be
            located.
        """
        for record in self.list_vcenters():
            if record.get('name') == name:
                return self.client.get_resource(record.get('href'))
        raise EntityNotFoundException('vCenter \'%s\' not found' % name)

    def list_external_networks(self):
        """List all external networks available in the system.

        :return: list of lxml.objectify.ObjectifiedElement objects which
            contains vmext:ExternalNetworkReference XML element representing
            the external network references.

        :rtype: list
        """
        ext_net_refs = self.client.get_linked_resource(
            self.extension.get_resource(), RelationType.DOWN,
            EntityType.EXTERNAL_NETWORK_REFS.value)

        if hasattr(ext_net_refs, 'ExternalNetworkReference'):
            return ext_net_refs.ExternalNetworkReference

        return []

    def get_external_network(self, name):
        """Fetch an external network resource identified by its name.

        :param str name: name of the external network to be retrieved.

        :return: an object containing EntityType.EXTERNAL_NETWORK XML data
            which represents an external network.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: EntityNotFoundException: If the named external network cannot
            be located.
        """
        ext_net_refs = self.list_external_networks()
        for ext_net in ext_net_refs:
            if ext_net.get('name') == name:
                return self.client.get_resource(ext_net.get('href'))
        raise EntityNotFoundException(
            'External network \'%s\' not found.' % name)

    def get_vxlan_network_pool(self, vxlan_network_pool_name):
        """[Deprecated] Fetch a vxlan_network_pool by its name.

        :param str vxlan_network_pool_name: name of the vxlan_network_pool.

        :return: an object containing NetworkPoolRecord XML element which
            represents a vxlan_network_pool.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: EntityNotFoundException: If the named vxlan_network_pool
            cannot be found.
        """
        name_filter = ('name', vxlan_network_pool_name)
        query = self.client.get_typed_query(
            ResourceType.NETWORK_POOL,
            query_result_format=QueryResultFormat.RECORDS,
            equality_filter=name_filter)
        records = list(query.execute())
        vxlan_network_pool_record = None
        for record in records:
            if vxlan_network_pool_name == record.get('name'):
                vxlan_network_pool_record = record
                break
        if vxlan_network_pool_record is not None:
            return vxlan_network_pool_record
        raise EntityNotFoundException(
            'vxlan_network_pool \'%s\' not found' % vxlan_network_pool_name)

    def get_res_by_name(self, resource_type, resource_name):
        """Fetch a reference to a resource by its name.

        :param pyvcloud.vcd.client.ResourceType resource_type: type of the
            resource.
        :param str resource_name: name of the resource.

        :return: an object containing sub-type of
            QueryResultFormat.REFERENCES XML data representing a reference to
            the resource.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: EntityNotFoundException: if the named resource cannot be
            found.
        """
        name_filter = ('name', resource_name)
        record = self.client.get_typed_query(
            resource_type.value,
            query_result_format=QueryResultFormat.REFERENCES,
            equality_filter=name_filter).find_unique()
        if resource_name == record.get('name'):
            return record
        else:
            raise EntityNotFoundException(
                'resource: \'%s\' name: \'%s\' not found' %
                resource_type.value, resource_name)

    def get_resource_pool_morefs(self, vc_name, vc_href, resource_pool_names):
        """Fetch list of morefs for a given list of resource_pool_names.

        :param str vc_name: vim_server name.
        :param str vc_href: vim_server href.
        :param list resource_pool_names: resource pool names as a list of
            strings.

        :return: morefs of resource pools.

        :rtype: list

        :raises: EntityNotFoundException: if any resource_pool_name cannot be
            found.
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
                    raise EntityNotFoundException(
                        'resource pool \'%s\' not Found' % resource_pool_name)
        return morefs

    def create_provider_vdc(self,
                            vim_server_name,
                            resource_pool_names,
                            storage_profiles,
                            pvdc_name,
                            is_enabled=None,
                            description=None,
                            highest_hw_vers=None,
                            vxlan_network_pool=None,
                            nsxt_manager_name=None):
        """Create a Provider Virtual Datacenter.

        :param str vim_server_name: vim_server_name (VC name).
        :param list resource_pool_names: list of resource_pool_names.
        :param list storage_profiles: (list): list of storageProfile namespace.
        :param str pvdc_name: name of PVDC to be created.
        :param bool is_enabled: flag, True to enable and False to disable.
        :param str description: description of pvdc.
        :param str highest_hw_vers: highest supported hw version number.
        :param str vxlan_network_pool: name of vxlan_network_pool.
        :param str nsxt_manager_name: name of nsx-t manager.

        :return: an object containing vmext:VMWProviderVdc XML element that
            represents the new provider VDC.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        vc_record = self.get_vcenter(vim_server_name)
        vc_href = vc_record.get('href')
        rp_morefs = self.get_resource_pool_morefs(vim_server_name, vc_href,
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
            network_pool_rec = self.get_res_by_name(ResourceType.NETWORK_POOL,
                                                    vxlan_network_pool)
            vx_href = network_pool_rec.get('href')
            vmw_prov_vdc_params.append(E_VMEXT.VxlanNetworkPool(href=vx_href))
        if nsxt_manager_name is not None:
            nsxt_manager_rec = self.get_res_by_name(ResourceType.NSXT_MANAGER,
                                                    nsxt_manager_name)
            nsxt_href = nsxt_manager_rec.get('href')
            vmw_prov_vdc_params.append(
                E_VMEXT.NsxTManagerReference(href=nsxt_href))
        if highest_hw_vers is not None:
            vmw_prov_vdc_params.append(
                E_VMEXT.HighestSupportedHardwareVersion(highest_hw_vers))
        if is_enabled is not None:
            vmw_prov_vdc_params.append(E_VMEXT.IsEnabled(is_enabled))
        for storage_profile in storage_profiles:
            vmw_prov_vdc_params.append(E_VMEXT.StorageProfile(storage_profile))
        random_username_suffix = uuid.uuid4().hex
        default_user = 'USR' + random_username_suffix[:8]
        default_pwd = 'PWD' + random_username_suffix[:8]
        vmw_prov_vdc_params.append(E_VMEXT.DefaultPassword(default_pwd))
        vmw_prov_vdc_params.append(E_VMEXT.DefaultUsername(default_user))

        return self.client.post_linked_resource(
            self.extension.get_resource(),
            rel=RelationType.ADD,
            media_type=EntityType.PROVIDER_VDC_PARAMS.value,
            contents=vmw_prov_vdc_params)

    def attach_resource_pools_to_provider_vdc(self,
                                              pvdc_name,
                                              resource_pool_names):
        """Attach Resource Pools to a Provider Virtual Datacenter.

        This function attaches one or more resource pools (RPs) to a
        Provider Virtual Datacenter (PVDC).

        Caveat: The current implementation of this function takes a list of RP
        "basenames" as input. A basename is the last element of a full
        pathname. For example, given a pathname /a/b/c, the basename of that
        pathname is "c". Since RP names are only required to have unique
        pathnames but not unique basenames, this function may not work
        correctly if there are non-unique RP basenames. Therefore, in order to
        use this function, all RP basenames must be unique. It is therefore up
        to the user of this function to be aware of this limitation and name
        their RPs appropriately. This limitation will be fixed in a future
        version of this function.

        :param str pvdc_name: name of the Provider Virtual Datacenter.
        :param list resource_pool_names: list or resource pool names.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is adding Resource Pools to the PVDC.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        provider_vdc = self.get_res_by_name(ResourceType.PROVIDER_VDC,
                                            pvdc_name)
        pvdc_resource = self.client.get_resource(provider_vdc.get('href'))
        pvdc_ext_href = get_admin_extension_href(pvdc_resource.get('href'))
        pvdc_ext_resource = self.client.get_resource(pvdc_ext_href)
        vc_name = pvdc_ext_resource.VimServer.get('name')
        vc_href = pvdc_ext_resource.VimServer.get('href')
        rp_morefs = self.get_resource_pool_morefs(vc_name, vc_href,
                                                  resource_pool_names)
        payload = E_VMEXT.UpdateResourcePoolSetParams()
        for rp_moref in rp_morefs:
            add_item = E_VMEXT.AddItem()
            add_item.append(
                E_VMEXT.VimServerRef(type=EntityType.VIRTUAL_CENTER.value,
                                     href=vc_href))
            add_item.append(E_VMEXT.MoRef(rp_moref))
            add_item.append(E_VMEXT.VimObjectType('RESOURCE_POOL'))
            payload.append(add_item)
        return self.client.post_linked_resource(
            resource=pvdc_ext_resource,
            rel=RelationType.UPDATE_RESOURCE_POOLS,
            media_type=EntityType.RES_POOL_SET_UPDATE_PARAMS.value,
            contents=payload)

    def detach_resource_pools_from_provider_vdc(self,
                                                pvdc_name,
                                                resource_pool_names):
        """Disable & Detach Resource Pools from a Provider Virtual Datacenter.

        This function deletes resource pools (RPs) from a Provider Virtual
        Datacenter (PVDC). In order to do this, the input "user-friendly" RP
        names must be translated into RP hrefs. This is a multi-step process.
        1) create a dictionary that maps RP names associated w/ this PVDC's
        backing VC to morefs.
        2) create a list of morefs_to_delete, using the dictionary created
        in step 1 -- filtered by the input set of RP names.
        3) create a dictionary that maps RP morefs associated w/ this PVDC to
        RP hrefs.
        4) Use the list of morefs_to_delete (created in step 2) to filter
        the list of RP hrefs created as a dictionary in step 3 to create
        the final payload.

        Note that in order to delete a RP, it must first be disabled. This is
        done for each RP to be deleted if the disable link is present (which
        indicates that the RP is enabled).

        Caveat: The current implementation of this function takes a list of RP
        "basenames" as input. A basename is the last element of a full
        pathname. For example, given a pathname /a/b/c, the basename of that
        pathname is "c". Since RP names are only required to have unique
        pathnames but not unique basenames, this function may not work
        correctly if there are non-unique RP basenames. Therefore, in order to
        use this function, all RP basenames must be unique. It is therefore up
        to the user of this function to be aware of this limitation and name
        their RPs appropriately. This limitation will be fixed in a future
        version of this function.

        :param str pvdc_name: name of the Provider Virtual Datacenter.
        :param list resource_pool_names: list or resource pool names.

        :return: an object containing EntityType.TASK XML data which represents
            the async task that is deleting Resource Pools fronm the PVDC.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: EntityNotFoundException: if any resource_pool_name cannot be
            found.
        :raises: ValidationError: if primary resource pool is input for
            deletion.
        """
        provider_vdc = self.get_res_by_name(ResourceType.PROVIDER_VDC,
                                            pvdc_name)
        pvdc_resource = self.client.get_resource(provider_vdc.get('href'))
        pvdc_ext_href = get_admin_extension_href(pvdc_resource.get('href'))
        pvdc_ext_resource = self.client.get_resource(pvdc_ext_href)
        vc_name = pvdc_ext_resource.VimServer.get('name')

        # find the RPs in use that are associated with the backing VC
        name_filter = ('vcName', vc_name)
        query = self.client.get_typed_query(
            ResourceType.RESOURCE_POOL.value,
            query_result_format=QueryResultFormat.RECORDS,
            equality_filter=name_filter)
        res_pools_in_use = {}
        for res_pool in list(query.execute()):
            res_pools_in_use[res_pool.get('name')] = res_pool.get('moref')

        morefs_to_delete = []
        for resource_pool_name in resource_pool_names:
            if resource_pool_name in res_pools_in_use.keys():
                morefs_to_delete.append(res_pools_in_use[resource_pool_name])
            else:
                raise EntityNotFoundException(
                    'resource pool \'%s\' not Found' % resource_pool_name)

        res_pools_in_pvdc = self.client.get_linked_resource(
            resource=pvdc_ext_resource,
            rel=RelationType.DOWN,
            media_type=EntityType.VMW_PROVIDER_VDC_RESOURCE_POOL_SET.value)

        pvdc_res_pools = {}
        if hasattr(res_pools_in_pvdc,
                   '{' + NSMAP['vmext'] + '}VMWProviderVdcResourcePool'):
            for res_pool in res_pools_in_pvdc.VMWProviderVdcResourcePool:
                pvdc_res_pools[res_pool.ResourcePoolVimObjectRef.MoRef] = \
                    res_pool

        res_pool_to_delete_refs = []
        for moref in morefs_to_delete:
            if moref not in pvdc_res_pools.keys():
                raise EntityNotFoundException(
                    'resource pool with moref \'%s\' not Found' % moref)
            else:
                res_pool = pvdc_res_pools[moref]
                if res_pool.get('primary') == 'true':
                    raise ValidationError(
                        'cannot delete primary respool with moref \'%s\' ' %
                        res_pool.ResourcePoolVimObjectRef.MoRef)
                else:
                    # disable the RP if it is enabled
                    links = get_links(resource=res_pool,
                                      rel=RelationType.DISABLE)
                    num_links = len(links)
                    if num_links == 1:
                        self.client.\
                            post_linked_resource(resource=res_pool,
                                                 rel=RelationType.DISABLE,
                                                 media_type=None,
                                                 contents=None)
                    res_pool_to_delete_refs.append(res_pool)

        payload = E_VMEXT.UpdateResourcePoolSetParams()
        for res_pool_ref in res_pool_to_delete_refs:
            del_item = E_VMEXT.DeleteItem(
                href=res_pool_ref.ResourcePoolRef.get('href'),
                type=EntityType.VMW_PROVIDER_VDC_RESOURCE_POOL.value)
            payload.append(del_item)
        return self.client.post_linked_resource(
            resource=pvdc_ext_resource,
            rel=RelationType.UPDATE_RESOURCE_POOLS,
            media_type=EntityType.RES_POOL_SET_UPDATE_PARAMS.value,
            contents=payload)

    def attach_vcenter(self,
                       vc_server_name,
                       vc_server_host,
                       vc_admin_user,
                       vc_admin_pwd,
                       is_enabled,
                       vc_root_folder=None,
                       nsx_server_name=None,
                       nsx_host=None,
                       nsx_admin_user=None,
                       nsx_admin_pwd=None):
        """Register (attach) a VirtualCenter server (also known as VimServer).

        :param str vc_server_name: vc server name (virtual center name).
        :param str vc_server_host: FQDN or IP address of vc host.
        :param str vc_admin_user: vc admin user.
        :param str vc_admin_pwd: vc admin password.
        :param str is_enabled: true if VC is to be enabled.
        :param str vc_root_folder: vc root folder.
        :param str nsx_server_name: NSX server name.
        :param str nsx_host: FQDN or IP address of NSX host.
        :param str nsx_admin_user: NSX admin user.
        :param str nsx_admin_pwd: NSX admin password.

        :return: an object containing REGISTER_VC_SERVER_PARAMS XML data that
            represents the newly registered (attached) VimServer.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        register_vc_server_params = E_VMEXT.RegisterVimServerParams()
        vc_server = E_VMEXT.VimServer(name=vc_server_name)
        vc_server.append(E_VMEXT.Username(vc_admin_user))
        vc_server.append(E_VMEXT.Password(vc_admin_pwd))
        vc_server.append(E_VMEXT.Url('https://' + vc_server_host + ':443'))
        vc_server.append(E_VMEXT.IsEnabled(is_enabled))
        if vc_root_folder is not None:
            vc_server.append(E_VMEXT.rootFolder(vc_root_folder))
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

    def enable_disable_vcenter(self, vc_name, enable_flag):
        """Enable or disable a Virtual Center (VC) server.

        :param str vc_name: name of VC server.
        :param boolean enable_flag: True means enable, False means disable.

        :return: an object containing EntityType.TASK XML data which represents
            the asynchronous task that is enabling or disabling the VC.

        rtype: lxml.objectify.ObjectifiedElement'
        """
        vc = self.get_vcenter(vc_name)
        if enable_flag:
            vc.IsEnabled = E_VMEXT.IsEnabled('true')
        else:
            vc.IsEnabled = E_VMEXT.IsEnabled('false')
        return self.client.\
            put_linked_resource(resource=vc,
                                rel=RelationType.EDIT,
                                media_type=EntityType.VIRTUAL_CENTER.value,
                                contents=vc)

    def detach_vcenter(self, vc_name):
        """Detach (unregister) a Virtual Center (VC) server.

        :param str vc_name: name of VC server.

        :return: an object containing XML data of the VC server
            specifically, EntityType.VIRTUAL_CENTER

        :rtype: lxml.objectify.ObjectifiedElement
        """
        vc = self.get_vcenter(vc_name)
        if vc.IsEnabled:
            raise InvalidStateException('VC must be disabled before detach.')

        return self.client.\
            post_linked_resource(resource=vc,
                                 rel=RelationType.UNREGISTER,
                                 media_type=None,
                                 contents=vc)

    def register_nsxt_manager(self,
                              nsxt_manager_name,
                              nsxt_manager_url,
                              nsxt_manager_username,
                              nsxt_manager_password,
                              nsxt_manager_description=None):
        """Register a NSX-T manager.

        :param str nsxt_manager_name: name of NSX-T manager.
        :param str nsxt_manager_url: URL of NSX-T manager server.
        :param str nsxt_manager_username: username of NSX-T manager admin.
        :param str nsxt_manager_password: password of NSX-T manager admin.
        :param str nsxt_manager_description: description of NSX-T manager.

        :return: an object containing XML data the newly registered NSX-T
            manager.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        payload = E_VMEXT.NsxTManager(name=nsxt_manager_name)
        if (nsxt_manager_description is not None):
            payload.append(E.Description(nsxt_manager_description))
        payload.append(E_VMEXT.Username(nsxt_manager_username))
        payload.append(E_VMEXT.Password(nsxt_manager_password))
        payload.append(E_VMEXT.Url(nsxt_manager_url))

        nsxt_manager_resource = self.client.get_linked_resource(
            resource=self.extension.get_resource(),
            rel=RelationType.DOWN,
            media_type=EntityType.NETWORK_MANAGERS.value)

        return self.client.\
            post_linked_resource(resource=nsxt_manager_resource,
                                 rel=RelationType.ADD,
                                 media_type=EntityType.NSXT_MANAGER.value,
                                 contents=payload)

    def unregister_nsxt_manager(self, nsxt_manager_name):
        """Un-register an NSX-T Manager.

        :param str nsxt_manager_name: name of the NSX-T manager.
        """
        nsxt_manager = self.get_res_by_name(ResourceType.NSXT_MANAGER,
                                            nsxt_manager_name).get('href')
        nsxt_manager_resource = self.client.get_resource(nsxt_manager)
        return \
            self.client.delete_linked_resource(nsxt_manager_resource,
                                               RelationType.REMOVE,
                                               EntityType.NSXT_MANAGER.value)

    def list_nsxt_managers(self):
        """Return list of all registered NSX-T managers.

        :return: NsxTManagerRecords.

        :rtype: generator object
        """
        query = self.client.get_typed_query(
            ResourceType.NSXT_MANAGER.value,
            query_result_format=QueryResultFormat.RECORDS)

        return query.execute()
