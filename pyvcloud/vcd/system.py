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

from pyvcloud.vcd.client import E
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import RelationType


class System(object):
    def __init__(self, client, admin_href=None, admin_resource=None):
        """
        Constructor for System objects
        :param client:  (pyvcloud.vcd.client): The client.
        :param admin_href: URI representing _WellKnownEndpoint.ADMIN
        :param admin_resource: (lxml.objectify.ObjectifiedElement): XML
        representation of admin_href
        """  # NOQA
        self.client = client
        self.admin_href = admin_href
        self.admin_resource = admin_resource
        if admin_resource is not None:
            self.admin_href = self.client.get_admin().get('href')

    def create_org(self, org_name, full_org_name):
        """
         Create new organization
        :param org_name: The name of the organization
        :param full_org_name: The fullname of the organization
        :return: (AdminOrgType) Created org object
         """  # NOQA
        if self.admin_resource is None:
            self.admin_resource = self.client.get_resource(self.admin_href)
        org_params = E.AdminOrg(
            E.FullName(full_org_name),
            E.Settings,
            name=org_name)
        return self.client.post_linked_resource(
            self.admin_resource,
            RelationType.ADD,
            EntityType.ADMIN_ORG.value,
            org_params)
