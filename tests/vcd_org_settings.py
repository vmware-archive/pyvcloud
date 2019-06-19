# VMware vCloud Director Python SDK
# Copyright (c) 2017 VMware, Inc. All Rights Reserved.
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

import unittest
import calendar
import time

from pyvcloud.vcd.system import System
from pyvcloud.vcd.test import TestCase
from pyvcloud.vcd.org_settings import OrgSettings

from lxml import etree

class TestOrgWithSettings(TestCase):

    def get_org_data(self):
        org_name = "UnitTest_"+ str(calendar.timegm(time.gmtime()))
        org_desc = "Unit test organization - " + str(calendar.timegm(time.gmtime()))
        return (org_name, org_desc)

    def test_01_create_org_vapp_lease_settings_not_default(self):
        ''' Create organization with non default values '''

        sys_admin = self.client.get_admin()
        system = System(self.client, admin_resource=sys_admin)

        # Test Data
        (org_name, org_desc) = self.get_org_data()
        vapp_lease_delete_on_storage_lease_expiration = True
        vapp_lease_deployment_lease_seconds = 18000
        vapp_lease_storage_lease_seconds = 7200

        # Set up settings object
        settings = OrgSettings()
        settings.set_vapp_lease_settings(vapp_lease_delete_on_storage_lease_expiration,
                                         vapp_lease_deployment_lease_seconds,
                                         vapp_lease_storage_lease_seconds)

        org = system.create_org(org_name,
                                org_desc,
                                settings=settings)

        assert org.get('name') == org_name

        vls = org.Settings.VAppLeaseSettings
        assert vls.DeleteOnStorageLeaseExpiration.text == str(vapp_lease_delete_on_storage_lease_expiration).lower()
        assert vls.DeploymentLeaseSeconds.text == str(vapp_lease_deployment_lease_seconds)
        assert vls.StorageLeaseSeconds.text ==  str(vapp_lease_storage_lease_seconds)

        # Cleanup delete the organization
        system.delete_org(org_name, True, True)

    def test_02_create_org_vapp_lease_settings_never_expire(self):
        ''' Create organization with lease never expire'''

        sys_admin = self.client.get_admin()
        system = System(self.client, admin_resource=sys_admin)

        # Test Data
        (org_name, org_desc) = self.get_org_data()
        vapp_lease_delete_on_storage_lease_expiration = False
        vapp_lease_deployment_lease_seconds = 0
        vapp_lease_storage_lease_seconds = 0

        # Set up settings object
        settings = OrgSettings()
        settings.set_vapp_lease_settings(vapp_lease_delete_on_storage_lease_expiration,
                                         vapp_lease_deployment_lease_seconds,
                                         vapp_lease_storage_lease_seconds)

        org = system.create_org(org_name,
                                org_desc,
                                settings=settings)

        assert org.get('name') == org_name

        vls = org.Settings.VAppLeaseSettings
        assert vls.DeleteOnStorageLeaseExpiration.text == str(vapp_lease_delete_on_storage_lease_expiration).lower()
        assert vls.DeploymentLeaseSeconds.text == str(vapp_lease_deployment_lease_seconds)
        assert vls.StorageLeaseSeconds.text ==  str(vapp_lease_storage_lease_seconds)

        # Cleanup delete the organization
        system.delete_org(org_name, True, True)

    def test_03_create_org_vapp__template_lease_settings_not_default(self):
        ''' Create organization with vApp template lease setting non default values'''

        sys_admin = self.client.get_admin()
        system = System(self.client, admin_resource=sys_admin)

        # Test Data
        (org_name, org_desc) = self.get_org_data()
        vapp_lease_template_delete_on_storage = True
        vapp_lease_template_delete_on_storage_lease_expiration = 7200
        vapp_lease_delete_on_storage_lease_expiration = False
        vapp_lease_deployment_lease_seconds = 0
        vapp_lease_storage_lease_seconds = 0

        # Set up settings object
        settings = OrgSettings()
        settings.set_vapp_lease_settings(vapp_lease_delete_on_storage_lease_expiration,
                                         vapp_lease_deployment_lease_seconds,
                                         vapp_lease_storage_lease_seconds)
        settings.set_vapp_template_lease_settings(vapp_lease_template_delete_on_storage,
                                                  vapp_lease_template_delete_on_storage_lease_expiration)

        org = system.create_org(org_name,
                                org_desc,
                                settings=settings)

        assert org.get('name') == org_name

        vtls = org.Settings.VAppTemplateLeaseSettings
        assert vtls.DeleteOnStorageLeaseExpiration.text == str(vapp_lease_template_delete_on_storage).lower()
        assert vtls.StorageLeaseSeconds.text == str(vapp_lease_template_delete_on_storage_lease_expiration)

        # Cleanup delete the organization
        system.delete_org(org_name, True, True)

    def test_04_create_org_ldap_settings_system(self):
        ''' Create organization with LDAP settings SYSTEM '''

        sys_admin = self.client.get_admin()
        system = System(self.client, admin_resource=sys_admin)

        # Test data
        (org_name, org_desc) = self.get_org_data()
        ldap_mode = 'SYSTEM'
        sys_users_ou = 'ou=Users,dc=example,dc=local'

        settings = OrgSettings()
        settings.set_org_ldap_settings( org_ldap_mode=ldap_mode,
                                        sys_users_ou=sys_users_ou
                                       )

        org = system.create_org(org_name,
                                org_desc,
                                settings=settings)
        ldap = org.Settings.OrgLdapSettings

        # Verifications
        assert org.get('name') == org_name
        assert ldap.OrgLdapMode.text == ldap_mode
        assert ldap.CustomUsersOu.text == sys_users_ou

        # Cleanup delete the organization
        system.delete_org(org_name, True, True)

    def test_05_create_org_ldap_settings_custom(self):
        ''' Create organization with LDAP settings CUSTOM '''

        sys_admin = self.client.get_admin()
        system = System(self.client, admin_resource=sys_admin)

        # Test data
        (org_name, org_desc) = self.get_org_data()
        ldap_mode = 'CUSTOM'
        custom_hostname = 'localhost'
        custom_port = 8080
        custom_is_ssl = True
        custom_is_ssl_accept_all = True
        custom_username = 'cn="ldap-admin", c="example", dc="com"'
        custom_password = 'veryscretpassword'
        custom_auth_mechanism = 'SIMPLE'
        custom_connector_type = 'OPEN_LDAP'
        custom_is_group_search_base_enabled = False
        custom_user_object_class = 'user'
        custom_user_object_identifier = 'objectGuid'
        custom_user_username = 'userPrincipalName'
        custom_user_email = 'test@testers.dom'
        custom_user_full_name = 'First Last'
        custom_user_given_name = 'First'
        custom_user_surname = 'Last'
        custom_user_telephone = '+61430088000'
        custom_user_group_membership_identifier = 'dn'
        custom_user_group_back_link_identifier = 'abc'
        custom_group_object_class = 'group'
        custom_group_object_identifier = 'dn'
        custom_group_group_name = 'cn'
        custom_group_membership = 'member'
        custom_group_membership_identifier = 'dn'
        custom_group_back_link_identifier = 'abc'
        custom_use_external_kerberos = False

        settings = OrgSettings()
        settings.set_org_ldap_settings(org_ldap_mode=ldap_mode,
                                       cus_hostname=custom_hostname,
                                       cus_port=custom_port,
                                       cus_is_ssl=custom_is_ssl,
                                       cus_is_ssl_accept_all=custom_is_ssl_accept_all,
                                       cus_username=custom_username,
                                       cus_password=custom_password,
                                       cus_auth_mechanism=custom_auth_mechanism,
                                       cus_connector_type=custom_connector_type,
                                       cus_is_grp_search_base_enabled=custom_is_group_search_base_enabled,
                                       cus_user_object_class=custom_user_object_class,
                                       cus_user_object_id=custom_user_object_identifier,
                                       cus_user_username=custom_user_username,
                                       cus_user_email=custom_user_email,
                                       cus_user_full_name=custom_user_full_name,
                                       cus_user_given_name=custom_user_given_name,
                                       cus_user_surname=custom_user_surname,
                                       cus_user_telephone=custom_user_telephone,
                                       cus_user_grp_membership_id=custom_user_group_membership_identifier,
                                       cus_user_grp_back_link_id=custom_user_group_back_link_identifier,
                                       cus_grp_object_class=custom_group_object_class,
                                       cus_grp_object_id=custom_group_object_identifier,
                                       cus_grp_grp_name=custom_group_group_name,
                                       cus_grp_membership=custom_group_membership,
                                       cus_grp_membership_id=custom_group_membership_identifier,
                                       cus_grp_back_link_id=custom_group_back_link_identifier,
                                       cus_use_external_kerberos=custom_use_external_kerberos)

        org = system.create_org(org_name,
                                org_desc,
                                settings=settings)
        ldap = org.Settings.OrgLdapSettings

        # Verifications
        assert org.get('name') == org_name
        assert ldap.OrgLdapMode.text == ldap_mode
        assert ldap.CustomOrgLdapSettings.HostName.text == custom_hostname
        assert int(ldap.CustomOrgLdapSettings.Port.text) == custom_port
        assert ldap.CustomOrgLdapSettings.IsSsl.text == str(custom_is_ssl).lower()
        assert ldap.CustomOrgLdapSettings.IsSslAcceptAll.text == str(custom_is_ssl_accept_all).lower()
        assert ldap.CustomOrgLdapSettings.UserName.text == custom_username
        # Password is not returned so no assert for password
        assert ldap.CustomOrgLdapSettings.AuthenticationMechanism.text == custom_auth_mechanism
        assert ldap.CustomOrgLdapSettings.IsGroupSearchBaseEnabled.text == str(custom_is_group_search_base_enabled).lower()
        assert ldap.CustomOrgLdapSettings.ConnectorType.text == custom_connector_type
        assert ldap.CustomOrgLdapSettings.UserAttributes.ObjectClass.text == custom_user_object_class
        assert ldap.CustomOrgLdapSettings.UserAttributes.ObjectIdentifier.text == custom_user_object_identifier
        assert ldap.CustomOrgLdapSettings.UserAttributes.UserName.text == custom_user_username
        assert ldap.CustomOrgLdapSettings.UserAttributes.Email.text == custom_user_email
        assert ldap.CustomOrgLdapSettings.UserAttributes.FullName.text == custom_user_full_name
        assert ldap.CustomOrgLdapSettings.UserAttributes.GivenName.text == custom_user_given_name
        assert ldap.CustomOrgLdapSettings.UserAttributes.Surname.text == custom_user_surname
        assert ldap.CustomOrgLdapSettings.UserAttributes.Telephone.text == custom_user_telephone
        assert ldap.CustomOrgLdapSettings.UserAttributes.GroupMembershipIdentifier.text == custom_user_group_membership_identifier
        assert ldap.CustomOrgLdapSettings.UserAttributes.GroupBackLinkIdentifier.text == custom_user_group_back_link_identifier
        assert ldap.CustomOrgLdapSettings.GroupAttributes.ObjectClass.text == custom_group_object_class
        assert ldap.CustomOrgLdapSettings.GroupAttributes.ObjectIdentifier.text == custom_group_object_identifier
        assert ldap.CustomOrgLdapSettings.GroupAttributes.GroupName.text == custom_group_group_name
        assert ldap.CustomOrgLdapSettings.GroupAttributes.Membership.text == custom_group_membership
        assert ldap.CustomOrgLdapSettings.GroupAttributes.MembershipIdentifier.text == custom_group_membership_identifier
        assert ldap.CustomOrgLdapSettings.GroupAttributes.BackLinkIdentifier.text == custom_group_back_link_identifier
        assert ldap.CustomOrgLdapSettings.UseExternalKerberos.text == str(custom_use_external_kerberos).lower()

        # Cleanup delete the organization
        system.delete_org(org_name, True, True)

if __name__ == '__main__':
    unittest.main()
