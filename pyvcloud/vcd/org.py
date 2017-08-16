# VMware vCloud Director Python SDK
# Copyright (c) 2014 VMware, Inc. All Rights Reserved.
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

from lxml import objectify
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.client import get_links
from pyvcloud.vcd.client import QueryResultFormat
from pyvcloud.vcd.client import RelationType
from pyvcloud.vcd.utils import to_dict


Organization = objectify.ElementMaker(
    annotate=False,
    namespace='',
    nsmap={None: "http://www.vmware.com/vcloud/v1.5"})


class Org(object):

    def __init__(self, client, org_href, is_admin=False):
        self.client = client
        self.endpoint = org_href
        self.endpoint_admin = org_href.replace('/api/org/', '/api/admin/org/')
        self.is_admin = is_admin

    def create_catalog(self, name, description):
        catalog = Organization.AdminCatalog(name=name)
        catalog.append(Organization.Description(description))
        return self.client.post_resource(
            self.endpoint_admin + '/catalogs',
            catalog,
            EntityType.ADMIN_CATALOG.value)

    def delete_catalog(self, name):
        org = self.client.get_resource(self.endpoint)
        links = get_links(org,
                          rel=RelationType.DOWN,
                          media_type=EntityType.CATALOG.value)
        for link in links:
            if name == link.name:
                admin_href = link.href.replace('/api/catalog/',
                                               '/api/admin/catalog/')
                return self.client.delete_resource(admin_href)
        raise Exception('Catalog not found.')

    def list_catalogs(self):
        if self.is_admin:
            resource_type = 'adminCatalog'
        else:
            resource_type = 'catalog'
        result = []
        q = self.client.get_typed_query(
            resource_type,
            query_result_format=QueryResultFormat.ID_RECORDS)
        records = list(q.execute())
        if len(records) == 0:
            result = 'No catalogs found.'
        else:
            for r in records:
                result.append(to_dict(r,
                                      resource_type=resource_type,
                                      exclude=['owner', 'org']))
        return result
