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
import os
import tempfile
import shutil
import requests
import tarfile
import urllib

from os.path import expanduser
from pyvcloud import _get_logger, Http, Log

#todo: get events
#todo: validate-blueprint
#todo: get execution details
#todo: cancel execution
#todo: get outputs of deployment
class Score(object):
    
    def __init__(self, url, org_url=None, token=None, version='5.7', verify=True, log=False):
        self.url = url
        self.org_url = org_url     
        self.token = token   
        self.version = version        
        self.verify = verify
        self.response = None        
        self.blueprints = BlueprintsClient(self)
        self.deployments = DeploymentsClient(self)
        self.executions = ExecutionsClient(self)
        self.events = EventsClient(self)
        self.logger = _get_logger() if log else None
        
    def get_headers(self):
        headers = {}
        headers["x-vcloud-authorization"] = self.token
        headers["x-vcloud-org-url"] = self.org_url                
        headers["x-vcloud-version"] = self.version        
        return headers
        
    def ping(self):
        self.response = Http.get(self.url + '/blueprints', headers=self.get_headers(), verify=self.verify, logger=self.logger)
        return self.response.status_code

class BlueprintsClient(object):

    def __init__(self, score, log=False):
        self.score = score
        self.logger = _get_logger() if log else None
        
    def list(self):
        self.score.response = Http.get(self.score.url + '/blueprints', headers=self.score.get_headers(), verify=self.score.verify, logger=self.logger)
        if self.score.response.status_code == requests.codes.ok:
            return json.loads(self.score.response.content)
            
    def get(self, blueprint_id):
        self.score.response = Http.get(self.score.url + '/blueprints/{0}'.format(blueprint_id), headers=self.score.get_headers(), verify=self.score.verify, logger=self.logger)
        if self.score.response.status_code == requests.codes.ok:
            return json.loads(self.score.response.content)
        
    def delete(self, blueprint_id):
        self.score.response = Http.delete(self.score.url + '/blueprints/{0}'.format(blueprint_id), headers=self.score.get_headers(), verify=self.score.verify, logger=self.logger)
        if self.score.response.status_code == requests.codes.ok:
            return json.loads(self.score.response.content)
            
    def upload(self, blueprint_path, blueprint_id):
        tempdir = tempfile.mkdtemp()
        try:
            tar_path = self._tar_blueprint(blueprint_path, tempdir)
            application_file = os.path.basename(blueprint_path)
            blueprint = self._upload(
                    tar_path,
                    blueprint_id=blueprint_id,
                    application_file_name=application_file)
            return blueprint
        finally:
            shutil.rmtree(tempdir)
                
    @staticmethod
    def _tar_blueprint(blueprint_path, tempdir):
        blueprint_path = expanduser(blueprint_path)
        blueprint_name = os.path.basename(os.path.splitext(blueprint_path)[0])
        blueprint_directory = os.path.dirname(blueprint_path)
        if not blueprint_directory:
            # blueprint path only contains a file name from the local directory
            blueprint_directory = os.getcwd()
        tar_path = os.path.join(tempdir, '{0}.tar.gz'.format(blueprint_name))
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(blueprint_directory, arcname=os.path.basename(blueprint_directory))            
        return tar_path    

    def _upload(self, tar_file,
                blueprint_id,
                application_file_name=None):
        query_params = {}
        if application_file_name is not None:
            query_params['application_file_name'] = \
                urllib.quote(application_file_name)

        uri = '/blueprints/{0}'.format(blueprint_id)
        url = '{0}{1}'.format(self.score.url, uri)
        headers = self.score.get_headers()
        with open(tar_file, 'rb') as f:
            self.score.response = Http.put(url, headers=headers, params=query_params,
                                           data=f, verify=self.score.verify, logger=self.logger)

        if self.score.response.status_code != 201:
            raise Exception(self.score.response.status_code)
            
        return self.score.response.json()        
        
class DeploymentsClient(object):

    def __init__(self, score, log=False):
        self.score = score
        self.logger = _get_logger() if log else None
        
    def list(self):
        self.score.response = Http.get(self.score.url + '/deployments', headers=self.score.get_headers(), verify=self.score.verify, logger=self.logger)
        if self.score.response.status_code == requests.codes.ok:
            return json.loads(self.score.response.content)
            
    def get(self, deployment_id):
        self.score.response = Http.get(self.score.url + '/deployments/{0}'.format(deployment_id), headers=self.score.get_headers(), verify=self.score.verify, logger=self.logger)
        if self.score.response.status_code == requests.codes.ok:
            return json.loads(self.score.response.content)
            
    def delete(self, deployment_id):
        self.score.response = Http.delete(self.score.url + '/deployments/{0}'.format(deployment_id), headers=self.score.get_headers(), verify=self.score.verify, logger=self.logger)
        if self.score.response.status_code == requests.codes.ok:
            return json.loads(self.score.response.content)
            
    def create(self, blueprint_id, deployment_id, inputs=None):
        assert blueprint_id
        assert deployment_id
        data = {
            'blueprint_id': blueprint_id
        }
        if inputs:
            data['inputs'] = inputs
        headers = self.score.get_headers()
        headers['Content-type'] = 'application/json'
        self.score.response = Http.put(self.score.url + '/deployments/{0}'.format(deployment_id), data=json.dumps(data), headers=headers, verify=self.score.verify, logger=self.logger)
        if self.score.response.status_code == requests.codes.ok:
            return json.loads(self.score.response.content)
            
            
class ExecutionsClient(object):

    def __init__(self, score, log=False):
        self.score = score
        self.logger = _get_logger() if log else None
        
    def list(self, deployment_id):
        params = {'deployment_id': deployment_id}
        self.score.response = Http.get(self.score.url + '/executions', headers=self.score.get_headers(), params=params,  verify=self.score.verify, logger=self.logger)
        if self.score.response.status_code == requests.codes.ok:
            return json.loads(self.score.response.content)
        else:
            Log.error(self.logger, 'list executions returned %s' % self.score.response.status_code)
            
    def start(self, deployment_id, workflow_id, parameters=None,
              allow_custom_parameters=False, force=False):
        assert deployment_id
        assert workflow_id
        data = {
            'deployment_id': deployment_id,
            'workflow_id': workflow_id,
            'parameters': parameters,
            'allow_custom_parameters': str(allow_custom_parameters).lower(),
            'force': str(force).lower()
        }
        headers = self.score.get_headers()
        headers['Content-type'] = 'application/json'
        self.score.response = Http.post(self.score.url + '/executions', headers=headers, data=json.dumps(data),  verify=self.score.verify, logger=self.logger)
        if self.score.response.status_code == requests.codes.ok:
            return json.loads(self.score.response.content)
            
class EventsClient(object):
    
    def __init__(self, score, log=False):
        self.score = score
        self.logger = _get_logger() if log else None
        
    def get(self, execution_id, from_event=0, batch_size=100, include_logs=False):
        assert execution_id
        data = {
            "execution_id": execution_id,
            "from": from_event,
            "size": batch_size,
            "include_logs": include_logs
        }
        headers = self.score.get_headers()
        headers['Content-type'] = 'application/json'
        self.score.response = Http.get(self.score.url + '/events', 
                                       headers=headers, data=json.dumps(data),  verify=self.score.verify, logger=self.logger)
        if self.score.response.status_code == requests.codes.ok:
            # print self.score.response.content
            json_events = json.loads(self.score.response.content)
            return json_events
        else:
            return []

