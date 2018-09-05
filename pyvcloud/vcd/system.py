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

    def create_org(self, org_name, full_org_name, is_enabled=False):
        """Create new organization.

        :param str org_name: name of the organization.
        :param str full_org_name: full name of the organization.
        :param bool is_enabled: enable organization if True

        :return: an object containing EntityType.ADMIN_ORG XML data which
            represents the newly created organization.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        if self.admin_resource is None:
            self.admin_resource = self.client.get_resource(self.admin_href)
        org_params = E.AdminOrg(
            E.FullName(full_org_name),
            E.IsEnabled(is_enabled),
            E.Settings,
            name=org_name)
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
