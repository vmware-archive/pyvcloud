# VMware vCloud Python SDK
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


import requests
import json
from xml.etree import ElementTree as ET
from pyvcloud import _get_logger, Http
from pyvcloud.schema.vcd.v1_5.schemas.vcloud import organizationListType
from pyvcloud.schema.vcd.v1_5.schemas.vcloud import queryRecordViewType
from pyvcloud.schema.vcd.v1_5.schemas.vcloud.vcloudType import \
     QueryResultRecordsType

class System(object):

    def __init__(self, session, verify, log=False):
        self.vcloud_session = session
        self.verify = verify
        self.response = None
        self.logger = _get_logger() if log else None

    def get_orgs(self):
        content_type = 'application/vnd.vmware.vcloud.orgList+xml'
        link = filter(lambda link: link.get_type() == content_type, self.vcloud_session.get_Link())
        orgs = []
        self.response = Http.get(link[0].get_href(), headers=self.vcloud_session.get_vcloud_headers(),
                                 verify=self.verify, logger=self.logger)
        if self.response.status_code == requests.codes.ok:
            organizations = organizationListType.parseString(self.response.content, True)
            for org in organizations.get_Org():
                orgs.append({'name': org.get_name(), 'href': org.get_href()})
            return orgs
        else:
            raise Exception(self.response.status_code)

    def add_org(self, org_name):
        pass

    def get_extensions(self):
        content_type = 'application/vnd.vmware.admin.vmwExtension+xml'
        link = filter(lambda link: link.get_type() == content_type, self.vcloud_session.get_Link())
        self.response = Http.get(link[0].get_href() + '/service/query', headers=self.vcloud_session.get_vcloud_headers(),
                                 verify=self.verify, logger=self.logger)
        if self.response.status_code == requests.codes.ok:
            doc = ET.fromstring(self.response.content)
            return doc
        else:
            raise Exception(self.response.status_code)

    def get_extension(self, name):
        content_type = 'application/vnd.vmware.admin.vmwExtension+xml'
        link = filter(lambda link: link.get_type() == content_type, self.vcloud_session.get_Link())
        self.response = Http.get(link[0].get_href() + '/service/query?pageSize=' + '1024',
                                 headers=self.vcloud_session.get_vcloud_headers(),
                                 verify=self.verify, logger=self.logger)
        if self.response.status_code == requests.codes.ok:
            result = queryRecordViewType.parseString(self.response.content, True)
            for t in result.get_Record():
                if name == t.get_name():
                    # return {'name': t.get_name(), 'href': t.get_href()}
                    self.response = Http.get(t.get_href(), headers=self.vcloud_session.get_vcloud_headers(),
                                             verify=self.verify, logger=self.logger)
                    if self.response.status_code == requests.codes.ok:
                        doc = ET.fromstring(self.response.content)
                        return doc
                        # print(self.response.content)
                        # return {'name': t.get_name(), 'href': t.get_href()}
            return None
        else:
            raise Exception(self.response.status_code)

    def register_extension(self, name, namespace, routing_key, patterns):
        api_filters = ''
        for pattern in patterns:
            api_filters += """
                <vmext:ApiFilter>
                    <vmext:UrlPattern>/api%s</vmext:UrlPattern>
                </vmext:ApiFilter>
            """ % pattern
        extension_metadata = """
        <vmext:Service xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:vmext="http://www.vmware.com/vcloud/extension/v1.5" name="%s">
           <vmext:Namespace>%s</vmext:Namespace>
           <vmext:Enabled>true</vmext:Enabled>
           <vmext:RoutingKey>%s</vmext:RoutingKey>
           <vmext:Exchange>vcdext</vmext:Exchange>
           <vmext:ApiFilters>
            %s
           </vmext:ApiFilters>
        </vmext:Service>
        """ % (name, namespace, routing_key, api_filters)
        content_type = 'application/vnd.vmware.admin.vmwExtension+xml'
        link = filter(lambda link: link.get_type() == content_type, self.vcloud_session.get_Link())
        self.response = Http.post(link[0].get_href() + '/service', headers=self.vcloud_session.get_vcloud_headers(),
                                  data=extension_metadata,
                                  verify=self.verify, logger=self.logger)
        if self.response.status_code == requests.codes.created:
            doc = ET.fromstring(self.response.content)
            return doc
        else:
            raise Exception(self.response.status_code)

    def enable_extension(self, name, href, enabled=True):
        extension_metadata = """
        <vmext:Service xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:vmext="http://www.vmware.com/vcloud/extension/v1.5" name="%s">
            <vmext:Namespace>%s</vmext:Namespace>
            <vmext:Enabled>%s</vmext:Enabled>
            <vmext:RoutingKey>%s</vmext:RoutingKey>
            <vmext:Exchange>vcdext</vmext:Exchange>
        </vmext:Service>
        """ % (name, name, 'true' if enabled else 'false', name)
        self.response = Http.put(href, headers=self.vcloud_session.get_vcloud_headers(),
                                 data=extension_metadata,
                                 verify=self.verify, logger=self.logger)
        if self.response.status_code == requests.codes.ok:
            return self.response.content
        else:
            raise Exception(self.response.status_code)

    def unregister_extension(self, name, href):
        self.response = Http.delete(href, headers=self.vcloud_session.get_vcloud_headers(),
                                 verify=self.verify, logger=self.logger)
        if self.response.status_code == requests.codes.no_content:
            return self.response.content
        else:
            raise Exception(self.response.status_code)
