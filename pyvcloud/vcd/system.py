# VMware vCloud Director Python SDK
# Copyright (c) 2017-2018 VMware, Inc. All Rights Reserved.
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

from pyvcloud.vcd.client import E
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import NSMAP
from pyvcloud.vcd.client import QueryResultFormat
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.exceptions import EntityNotFoundException
from pyvcloud.vcd.exceptions import InvalidParameterException
from pyvcloud.vcd.utils import get_admin_href


class System(object):
    def __init__(self, client, admin_href=None, admin_resource=None):
        """Constructor for System objects.

        :param pyvcloud.vcd.client.Client client: the client that will be used
            to make REST calls to vCD.
        :param str admin_href: URI representing _WellKnownEndpoint.ADMIN.
        :param lxml.objectify.ObjectifiedElement admin_resource: an object
            containing EntityType.ADMIN XML data.
        """
        self.client = client
        if admin_href is None and admin_resource is None:
            raise InvalidParameterException(
                "System initialization failed as arguments are either "
                "invalid or None")
        self.admin_href = admin_href
        self.admin_resource = admin_resource
        if admin_resource is not None:
            self.admin_href = self.client.get_admin().get('href')

    def create_org(self, org_name, full_org_name, is_enabled=False, org_settings={}):
        """Create new organization.
        Syntax: def create_org(self, org_name, full_org_name, is_enabled=False, org_settings={})
        :param str org_name: name of the organization.
        :param str full_org_name: full name of the organization.
        :param bool is_enabled: enable organization if True.
        :param dict org_settings: dictionary of settings used to customize the org creation
        :return: an object containing EntityType.ADMIN_ORG XML data which
            represents the newly created organization.

        :rtype: lxml.objectify.ObjectifiedElement
        """

        '''
        org_settings is a dictionary made of other dictionaries with the following key value pairs
        Dictionary org_general_settings:
            can_publish_catalogs: allow publishing catalogs
            can_publish_externally: allow publishing catalogs externally
            can_subscribe: allow to subscribe to catalogs
            deployed_vmquota: default quotas for how many VMs a User can power on in this organization
            stored_vmquota: default quotas for how many VMs a User can store in this organization
            use_server_boot_sequence: allow use of server boot sequence
            delay_after_power_on_seconds: specify a delay after power on the VMs
        Dictionary vapp_lease_settings:
            delete_on_storage_lease_expiration: allow to delete vapp at the end of the lease
            deployment_lease_seconds: specify length of the lease for a vapp
            storage_lease_seconds: specify length of the lease for a vapp on the storage
        Dictionary vapp_template_lease_settings:
            delete_template_on_storage_lease_expiration: allow to delete vapp template at the end of the lease
            storage_template_lease_seconds: specify length of the lease for a vapp template on the storage
        Dictionary org_ldap_settings:
              org_ldap_mode: determine if Ldap is enabled ("CUSTOM", "SYSTEM") or not ("NONE")
              (if org_ldap_mode different from "NONE", please refer to the the API docs
              https://pubs.vmware.com/vca/topic/com.vmware.vcloud.api.reference.doc_56/doc/types/CustomOrgLdapSettingsType.html
              for the description of all the fields needed)
              Dictionary 'user_attributes' and 'group_attributes' have defaults values so don't have to be specified from the
              playbook/role in case OrgLdapMode value is not NONE, as the defaults values defined below in default_settings
              will be used instead.
        Dictionary org_email_settings:
            is_default_smtp_server: specify if using the default smtp server
            is_default_org_email: specify if using the default organization's email
            from_email_address: specify email address
            default_subject_prefix: specify default subject for the email
            is_alert_to_all_admin: allow to send the alert to all admins
        Dictionary org_federation_settings:
            saml_metadata: XML content with the SAML Metdata
            enabled: boolean that specifies if the SAML authentication is enabled or not
        '''

        # default_settings is a helper dictionary that containes the API defaults when creating an org
        default_settings = {
            "org_general_settings": {
                "can_publish_catalogs": True,
                "can_publish_externally": False,
                "can_subscribe": False,
                "deployed_vmquota": 10,
                "stored_vmquota": 15,
                "use_server_boot_sequence": False,
                "delay_after_power_on_seconds": 1,
            },
            "vapp_lease_settings": {
                "delete_on_storage_lease_expiration": False,
                "deployment_lease_seconds": 604800,
                "storage_lease_seconds": 2592000,
            },
            "vapp_template_lease_settings": {
                "delete_template_on_storage_lease_expiration": False,
                "storage_template_lease_seconds": 2592000,
            },
            "org_ldap_settings": {
                "OrgLdapMode": "NONE",
            },
            "org_email_settings": {
                "is_default_smtp_server": True,
                "is_default_org_email": True,
                "from_email_address": "",
                "default_subject_prefix": " ",
                "is_alert_to_all_admin": True,
            },
            "org_federation_settings": {
                "saml_metadata": "",
                "enabled": False,
            },
        }
        # create the org_settings dict for the API consumption if none is provided or the one provided is not complete
        for key1 in default_settings:
            if key1 not in org_settings:
                org_settings[key1] = default_settings[key1]
            elif isinstance(default_settings[key1], dict):
                for key2 in default_settings[key1]:
                    if key2 not in org_settings[key1]:
                        org_settings[key1][key2] = default_settings[key1][key2]

        if self.admin_resource is None:
            self.admin_resource = self.client.get_resource(self.admin_href)

        org_params = E.AdminOrg(
            E.FullName(full_org_name),
            E.IsEnabled(is_enabled),
            name=org_name)
        # Build the org_params_settings object
        org_params_settings = E.Settings()
        org_params_settings.OrgGeneralSettings = E.OrgGeneralSettings(
            E.CanPublishCatalogs(org_settings.get("org_general_settings").get("can_publish_catalogs")),
            E.CanPublishExternally(org_settings.get("org_general_settings").get("can_publish_externally")),
            E.CanSubscribe(org_settings.get("org_general_settings").get("can_subscribe")),
            E.DeployedVMQuota(org_settings.get("org_general_settings").get("deployed_vmquota")),
            E.StoredVmQuota(org_settings.get("org_general_settings").get("stored_vmquota")),
            E.UseServerBootSequence(org_settings.get("org_general_settings").get("use_server_boot_sequence")),
            E.DelayAfterPowerOnSeconds(
                org_settings.get("org_general_settings").get("delay_after_power_on_seconds"))
        )
        org_params_settings.VAppLeaseSettings = E.VAppLeaseSettings(
            E.DeleteOnStorageLeaseExpiration(
                org_settings.get("vapp_lease_settings").get("delete_on_storage_lease_expiration")),
            E.DeploymentLeaseSeconds(org_settings.get("vapp_lease_settings").get("deployment_lease_seconds")),
            E.StorageLeaseSeconds(org_settings.get("vapp_lease_settings").get("storage_lease_seconds"))
        )
        org_params_settings.VAppTemplateLeaseSettings = E.VAppTemplateLeaseSettings(
            E.DeleteOnStorageLeaseExpiration(org_settings.get("vapp_template_lease_settings").get(
                "delete_template_on_storage_lease_expiration")),
            E.StorageLeaseSeconds(
                org_settings.get("vapp_template_lease_settings").get("storage_template_lease_seconds"))
        )
        if org_settings.get("org_ldap_settings").get("org_ldap_mode") != 'NONE':
            org_params_settings.OrgLdapSettings = E.OrgLdapSettings(
            E.OrgLdapMode(org_settings.get("org_ldap_settings").get("org_ldap_mode")),
            E.CustomOrgLdapSettings(
                E.HostName(org_settings.get("org_ldap_settings").get("custom_org_ldap_settings").get("hostname")),
                E.Port(org_settings.get("org_ldap_settings").get("custom_org_ldap_settings").get("port")),
                E.IsSsl(org_settings.get("org_ldap_settings").get("custom_org_ldap_settings").get("is_ssl")),
                E.IsSslAcceptAll(
                    org_settings.get("org_ldap_settings").get("custom_org_ldap_settings").get("is_ssl_accept_all")),
                E.Realm(org_settings.get("org_ldap_settings").get("custom_org_ldap_settings").get("realm")),
                E.SearchBase(
                    org_settings.get("org_ldap_settings").get("custom_org_ldap_settings").get("search_base")),
                E.UserName(org_settings.get("org_ldap_settings").get("custom_org_ldap_settings").get("username")),
                E.Password(org_settings.get("org_ldap_settings").get("custom_org_ldap_settings").get("password")),
                E.AuthenticationMechanism(org_settings.get("org_ldap_settings").get("custom_org_ldap_settings").get(
                    "authentication_mechanism")),
                E.GroupSearchBase(
                    org_settings.get("org_ldap_settings").get("custom_org_ldap_settings").get("group_search_base")),
                E.IsGroupSearchBaseEnabled(org_settings.get("org_ldap_settings").get("custom_org_ldap_settings").get(
                    "is_group_search_base_enabled")),
                E.ConnectorType(
                    org_settings.get("org_ldap_settings").get("custom_org_ldap_settings").get("connector_type")),
                E.UserAttributes(
                    E.ObjectClass(org_settings.get("org_ldap_settings").get("custom_org_ldap_settings").get(
                        "user_attributes").get("object_class")),
                    E.ObjectIdentifier(org_settings.get("org_ldap_settings").get("custom_org_ldap_settings").get(
                        "user_attributes").get("object_identifier")),
                    E.UserName(org_settings.get("org_ldap_settings").get("custom_org_ldap_settings").get(
                        "user_attributes").get("username")),
                    E.Email(org_settings.get("org_ldap_settings").get("custom_org_ldap_settings").get(
                        "user_attributes").get("email")),
                    E.FullName(org_settings.get("org_ldap_settings").get("custom_org_ldap_settings").get(
                        "user_attributes").get("fullname")),
                    E.GivenName(org_settings.get("org_ldap_settings").get("custom_org_ldap_settings").get(
                        "user_attributes").get("given_name")),
                    E.Surname(org_settings.get("org_ldap_settings").get("custom_org_ldap_settings").get(
                        "user_attributes").get("surname")),
                    E.Telephone(org_settings.get("org_ldap_settings").get("custom_org_ldap_settings").get(
                        "user_attributes").get("telephone")),
                    E.GroupMembershipIdentifier(
                        org_settings.get("org_ldap_settings").get("custom_org_ldap_settings").get(
                            "user_attributes").get("group_membership_identifier")),
                    E.GroupBackLinkIdentifier(
                        org_settings.get("org_ldap_settings").get("custom_org_ldap_settings").get(
                            "user_attributes").get("group_back_link_identifier"))
                ),
                E.GroupAttributes(
                    E.ObjectClass(org_settings.get("org_ldap_settings").get("custom_org_ldap_settings").get(
                        "group_attributes").get("object_class")),
                    E.ObjectIdentifier(org_settings.get("org_ldap_settings").get("custom_org_ldap_settings").get(
                        "group_attributes").get("object_identifier")),
                    E.GroupName(org_settings.get("org_ldap_settings").get("custom_org_ldap_settings").get(
                        "group_attributes").get("group_name")),
                    E.Membership(org_settings.get("org_ldap_settings").get("custom_org_ldap_settings").get(
                        "group_attributes").get("membership")),
                    E.MembershipIdentifier(org_settings.get("org_ldap_settings").get("custom_org_ldap_settings").get(
                        "group_attributes").get("membership_identifier")),
                    E.BackLinkIdentifier(org_settings.get("org_ldap_settings").get("custom_org_ldap_settings").get(
                        "group_attributes").get("backLink_identifier"))
                ),
                E.UseExternalKerberos(
                    org_settings.get("org_ldap_settings").get("custom_org_ldap_settings").get("use_external_kerberos"))
            )
        )
        org_params_settings.OrgEmailSettings = E.OrgEmailSettings(
            E.IsDefaultSmtpServer(org_settings.get("org_email_settings").get("is_default_smtp_server")),
            E.IsDefaultOrgEmail(org_settings.get("org_email_settings").get("is_default_org_email")),
            E.FromEmailAddress(org_settings.get("org_email_settings").get("from_email_address")),
            E.DefaultSubjectPrefix(org_settings.get("org_email_settings").get("default_subject_prefix")),
            E.IsAlertEmailToAllAdmins(org_settings.get("org_email_settings").get("is_alert_to_all_admin"))
        )

        org_params_settings.OrgFederationSettings = E.OrgFederationSettings(
            E.SAMLMetadata(org_settings.get("org_federation_settings").get("saml_metadata")),
            E.Enabled(org_settings.get("org_federation_settings").get("enabled"))
        )

        # Build the org_params object
        org_params.Settings = org_params_settings
        return self.client.post_linked_resource(
            self.admin_resource, RelationType.ADD, EntityType.ADMIN_ORG.value,
            org_params)

    def delete_org(self, org_name, force=None, recursive=None):
        """Delete an organization.

        :param str org_name: name of the org to be deleted.
        :param bool force: pass force=True along with recursive=True to remove
            an organization and any objects it contains, regardless of their
            state.
        :param bool recursive: pass recursive=True to remove an organization
            and any objects it contains that are in a state that normally
            allows removal.
        """
        org_resource = self.client.get_org_by_name(org_name)
        org_admin_href = get_admin_href(org_resource.get('href'))
        return self.client.delete_resource(org_admin_href, force, recursive)

    def list_provider_vdcs(self):
        """List provider vdcs in the system organization.

        :return: a list of object containing ProviderVdcReference XML data.

        :rtype: list
        """
        if self.admin_resource is None:
            self.admin_resource = self.client.get_resource(self.admin_href)
        if hasattr(self.admin_resource, 'ProviderVdcReferences') and \
           hasattr(self.admin_resource.ProviderVdcReferences,
                   'ProviderVdcReference'):
            return self.admin_resource.ProviderVdcReferences.\
                ProviderVdcReference
        else:
            return []

    def get_provider_vdc(self, name):
        """Fetch a provider VDC by name in the system organization.

        :return: an object containing ProviderVdcReference XML element which
            refers to the provider vdc.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: EntityNotFoundException: if the named provider vdc can not be
            found.
        """
        for pvdc in self.list_provider_vdcs():
            if pvdc.get('name') == name:
                return pvdc
        raise EntityNotFoundException('Provider VDC \'%s\' not found or '
                                      'access to resource is forbidden' % name)

    def list_provider_vdc_storage_profiles(self, name=None):
        """List provider VDC storage profiles in the system organization.

        :return: a list of ProviderVdcStorageProfile items

        :rtype: list
        """
        name_filter = None
        if name is not None:
            name_filter = ('name', name)

        q = self.client.get_typed_query(
            'providerVdcStorageProfile',
            query_result_format=QueryResultFormat.RECORDS,
            equality_filter=name_filter)

        return list(q.execute())

    def get_provider_vdc_storage_profile(self, name):
        """Return a provider VDC storage profile by name in the system org.

        :return: ProviderVdcStorageProfile item.

        :raises: EntityNotFoundException: if the named provider vdc can not be
            found.
        """
        for profile in self.list_provider_vdc_storage_profiles(name):
            if profile.get('name') == name:
                return profile
        raise EntityNotFoundException('Storage profile \'%s\' not found or '
                                      'access to resource is forbidden.' %
                                      name)

    def list_network_pools(self):
        """List network pools in the system organization.

        :return: a list of lxml.objectify.ObjectifiedElement containing
            NetworkPoolReference XML elements.

        :rtype: list
        """
        resource = self.client.get_extension()
        result = self.client.get_linked_resource(
            resource, RelationType.DOWN,
            EntityType.NETWORK_POOL_REFERENCES.value)
        if hasattr(result, '{' + NSMAP['vmext'] + '}NetworkPoolReference'):
            return result.NetworkPoolReference
        else:
            return []

    def get_network_pool_reference(self, name):
        """Return a network pool by name in the system organization.

        :return: an object containing NetworkPoolReference XML element.

        :rtype: lxml.objectify.ObjectifiedElement

        :raises: EntityNotFoundException: if the named network pool can not be
            found.
        """
        for item in self.list_network_pools():
            if item.get('name') == name:
                return item
        raise EntityNotFoundException('Network pool \'%s\' not found or '
                                      'access to resource is forbidden' % name)

