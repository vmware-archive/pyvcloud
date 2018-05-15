# VMware vCloud Director Python SDK
# Copyright (c) 2018 VMware, Inc. All Rights Reserved.
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

from pyvcloud.vcd.platform import Platform
from pyvcloud.vcd.test import TestCase
from pyvcloud.vcd.utils import to_dict


class TestNSXT(TestCase):

    def register_nsxt(self):
        platform = Platform(self.client)

        nsxt = platform.register_nsxt_manager(
            nsxt_manager_name=self.config['vcd']['nsxTManagerName'],
            nsxt_manager_url=self.config['vcd']['nsxTManagerHostURL'],
            nsxt_manager_username=self.config['vcd']['nsxTAdminUser'],
            nsxt_manager_password=self.config['vcd']['nsxTAdminPwd'],
            nsxt_manager_description=self.config['vcd']['nsxTDescription'])
        assert self.config['vcd']['nsxTManagerName'] == nsxt.get('name')

    def unregister_nsxt(self):
        platform = Platform(self.client)

        platform.unregister_nsxt_manager(
            nsxt_manager_name=self.config['vcd']['nsxTManagerName'])

    def list_nsxt_managers(self):
        platform = Platform(self.client)

        query = platform.list_nsxt_managers()
        result = []
        for record in list(query):
            result.append(
                to_dict(
                    record,
                    exclude=['href']))
        print(result)


if __name__ == '__main__':
    unittest.main()
