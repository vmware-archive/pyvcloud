# VMware vCloud Director Python SDK
# Copyright (c) 2014-2018 VMware, Inc. All Rights Reserved.
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
from pyvcloud.vcd.utils import Transform


class OrgSettings(object):
    """Representation of Settings resource for organization."""

    def __init__(self):
        self.vapp_lease_settings = None
        self.vapp_template_lease_settings = None
        self.ldap_settings = None

    def get_settings(self):
        """Generates the objectified resource of Settings and return.

        :return: returns objectified element of Settings

        :rtype: lxml.objectify.ObjectifiedElement
        """
        settings = E.Settings()

        if self.vapp_lease_settings is not None:
            settings.append(self.vapp_lease_settings)

        if self.vapp_template_lease_settings is not None:
            settings.append(self.vapp_template_lease_settings)

        if self.ldap_settings is not None:
            settings.append(self.ldap_settings)

        return settings

    def set_vapp_lease_settings(self,
                                delete_on_storage_expiration=None,
                                deployment_lease_seconds=None,
                                storage_lease_seconds=None):
        """Generates VAppLeaseSettings objectified resource.

        :param bool delete_on_storage_expiration: storage cleanup policy
        :param int deployment_lease_seconds: maximum runtiime lease in seconds
        :param int storage_lease_seconds: maximu storage lease in seconds
        """
        self.vapp_lease_settings = E.VAppLeaseSettings()

        if delete_on_storage_expiration is not None:
            self.vapp_lease_settings.append(
                E.DeleteOnStorageLeaseExpiration(delete_on_storage_expiration))

        if deployment_lease_seconds is not None:
            self.vapp_lease_settings.append(
                E.DeploymentLeaseSeconds(int(deployment_lease_seconds)))

        if storage_lease_seconds is not None:
            self.vapp_lease_settings.append(
                E.StorageLeaseSeconds(int(storage_lease_seconds)))

    def set_vapp_template_lease_settings(
            self,
            delete_on_storage_lease_expiration=None,
            storage_lease_seconds=None):
        """Generates VAppTemplateLeaseSettings objectified resource.

        Note: VAppTemplateLeaseSettings configuration requires
              VAppLeaseSettings resource with values. Otherwise
              it result in 500/INTERNAL_SERVER_ERROR.

        :param bool delete_on_storage_lease_expiration: storage cleanup
        :param int storage_lease_seconds: maximum storage lease
        """
        self.vapp_template_lease_settings = E.VAppTemplateLeaseSettings()

        if delete_on_storage_lease_expiration is not None:
            self.vapp_template_lease_settings.append(
                E.DeleteOnStorageLeaseExpiration(
                    delete_on_storage_lease_expiration))

        if storage_lease_seconds is not None:
            self.vapp_template_lease_settings.append(
                E.StorageLeaseSeconds(int(storage_lease_seconds)))

    def set_org_ldap_settings(self,
                              org_ldap_mode=None,
                              sys_users_ou=None,
                              cus_hostname=None,
                              cus_port=None,
                              cus_is_ssl=None,
                              cus_is_ssl_accept_all=None,
                              cus_truststore=None,
                              cus_relam=None,
                              cus_search_base=None,
                              cus_username=None,
                              cus_password=None,
                              cus_auth_mechanism=None,
                              cus_group_search_base=None,
                              cus_is_grp_search_base_enabled=None,
                              cus_connector_type=None,
                              cus_user_object_class=None,
                              cus_user_object_id=None,
                              cus_user_username=None,
                              cus_user_email=None,
                              cus_user_full_name=None,
                              cus_user_given_name=None,
                              cus_user_surname=None,
                              cus_user_telephone=None,
                              cus_user_grp_membership_id=None,
                              cus_user_grp_back_link_id=None,
                              cus_grp_object_class=None,
                              cus_grp_object_id=None,
                              cus_grp_grp_name=None,
                              cus_grp_membership=None,
                              cus_grp_membership_id=None,
                              cus_grp_back_link_id=None,
                              cus_use_external_kerberos=None):

        # Note: At the moment model does not support restricting
        #       fields for specific versions. This can be enhanced
        #       by updating model and transform utility. User must
        #       provide the correct parameters as supported by the version
        data = [
            {'OrgLdapMode': org_ldap_mode},
            {'CustomUsersOu': sys_users_ou},
            {'CustomOrgLdapSettings': [
                {'HostName': cus_hostname},
                {'Port': cus_port},
                {'IsSsl': cus_is_ssl},
                {'IsSslAcceptAll': cus_is_ssl_accept_all},
                {'CustomTruststore': cus_truststore},
                {'Realm': cus_relam},
                {'SearchBase': cus_search_base},
                {'UserName': cus_username},
                {'Password': cus_password},
                {'AuthenticationMechanism': cus_auth_mechanism},
                {'GroupSearchBase': cus_group_search_base},
                {'IsGroupSearchBaseEnabled': cus_is_grp_search_base_enabled},
                {'ConnectorType': cus_connector_type},
                {'UserAttributes': [
                    {'ObjectClass': cus_user_object_class},
                    {'ObjectIdentifier': cus_user_object_id},
                    {'UserName': cus_user_username},
                    {'Email': cus_user_email},
                    {'FullName': cus_user_full_name},
                    {'GivenName': cus_user_given_name},
                    {'Surname': cus_user_surname},
                    {'Telephone': cus_user_telephone},
                    {'GroupMembershipIdentifier': cus_user_grp_membership_id},
                    {'GroupBackLinkIdentifier': cus_user_grp_back_link_id}
                ]},
                {'GroupAttributes': [
                    {'ObjectClass': cus_grp_object_class},
                    {'ObjectIdentifier': cus_grp_object_id},
                    {'GroupName': cus_grp_grp_name},
                    {'Membership': cus_grp_membership},
                    {'MembershipIdentifier': cus_grp_membership_id},
                    {'BackLinkIdentifier': cus_grp_back_link_id}
                ]},
                {'UseExternalKerberos': cus_use_external_kerberos}]}]

        transform = Transform()
        (self.ldap_settings, flag_children_added) = \
            transform.list_to_objectify(data, 'OrgLdapSettings')
