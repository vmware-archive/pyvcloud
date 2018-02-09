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

import os
import unittest
import yaml
from pyvcloud.vcd.client import BasicLoginCredentials
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.test import TestCase

class UpdateCatalog(TestCase):

    def test_create_catalog(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        catalog = org.create_catalog(self.config['vcd']['catalog'], 'test catalog')
        assert self.config['vcd']['catalog'] == catalog.get('name')

    def test_update_catalog(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        catalog = org.update_catalog(self.config['vcd']['catalog'],
           self.config['vcd']['new_name'], self.config['vcd']['new_desc'])
        assert self.config['vcd']['new_name'] == catalog.get('name')
        assert self.config['vcd']['new_desc'] == catalog['Description']

if __name__ == '__main__':
    unittest.main()
