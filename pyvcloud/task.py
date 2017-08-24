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

from pyvcloud import _get_logger
from pyvcloud import Http
from pyvcloud.schema.vcd.v1_5.schemas.vcloud import tasksListType
from pyvcloud.schema.vcd.v1_5.schemas.vcloud import taskType
import requests
from urlparse import urlparse


class Task(object):

    statuses = ['running',
                'success',
                'error',
                'aborted',
                'queued',
                'canceled',
                'preRunning']

    def __init__(self, session, verify, log=False):
        self.vcloud_session = session
        self.verify = verify
        self.response = None
        self.logger = _get_logger() if log else None

    def get_tasks(self, status=statuses[0]):
        if self.vcloud_session and self.vcloud_session.organization:
            refs = filter(lambda ref:
                    ref.type_ == 'application/vnd.vmware.vcloud.tasksList+xml',
                    self.vcloud_session.organization.Link)
            if len(refs) == 1:
                self.response = Http.get(refs[0].href,
                    headers=self.vcloud_session.get_vcloud_headers(),
                    verify=self.verify,
                    logger=self.logger)
                if self.response.status_code == requests.codes.ok:
                    return tasksListType.parseString(self.response.content,
                                                     True)
                else:
                    raise Exception(self.response.status_code)
        return None

    def create_or_update_task(self,
                              status,
                              namespace,
                              operation_name,
                              operation_description,
                              owner_href,
                              owner_name,
                              owner_type,
                              user_id,
                              user_name,
                              progress,
                              details,
                              org_id=None,
                              task_id=None):
        if self.vcloud_session:
            o = urlparse(self.vcloud_session.url)
            api_url = '%s://%s%s' % (o.scheme, o.netloc, '/api')
            if progress is None:
                progress_indicator = ''
            else:
                progress_indicator = 'progress="%s"' % progress
            data = """
                <Task
                   xmlns="http://www.vmware.com/vcloud/v1.5"
                   status="{status}"
                   serviceNamespace="{namespace}"
                   type="application/vnd.vmware.vcloud.task+xml"
                   operation="{operation_description}"
                   operationName="{operation_name}"
                   {progress_indicator}
                   name="task">
                   <Owner href="{owner_href}" name="{owner_name}"
                          type="{owner_type}"/>
                   <User href="{api_url}/admin/user/{user_id}"
                         name="{user_name}"
                         type="application/vnd.vmware.admin.user+xml"/>
                   <Details>"{details}"</Details>
                </Task>
            """.format(status=status,
                       namespace=namespace,
                       operation_description=operation_description,
                       operation_name=operation_name,
                       progress_indicator=progress_indicator,
                       api_url=api_url,
                       details=details,
                       owner_href=owner_href,
                       owner_name=owner_name,
                       owner_type=owner_type,
                       user_id=user_id,
                       user_name=user_name)
            if task_id is None:
                link = '%s/tasksList/%s' % (api_url, org_id)
                self.response = Http.post(link,
                    headers=self.vcloud_session.get_vcloud_headers(),
                    verify=self.verify,
                    logger=self.logger,
                    data=data)
            else:
                link = '%s/task/%s' % (api_url, task_id)
                self.response = Http.put(link,
                    headers=self.vcloud_session.get_vcloud_headers(),
                    verify=self.verify,
                    logger=self.logger,
                    data=data)
            if self.response.status_code == requests.codes.ok:
                return taskType.parseString(self.response.content, True)
            else:
                raise Exception(self.response.status_code)
        return None

    def get_task(self, task_id):
        if self.vcloud_session:
            o = urlparse(self.vcloud_session.url)
            link = '%s://%s%s/%s' % (o.scheme, o.netloc, '/api/task', task_id)
            self.response = Http.get(link,
                headers=self.vcloud_session.get_vcloud_headers(),
                verify=self.verify,
                logger=self.logger)
            if self.response.status_code == requests.codes.ok:
                return taskType.parseString(self.response.content, True)
            else:
                raise Exception(self.response.status_code)
        return None
