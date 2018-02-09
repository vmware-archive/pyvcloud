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

from pyvcloud.vcd.system import System
from pyvcloud.vcd.test import TestCase


class TestSystem(TestCase):
    def test_create_org(self):
        sys_admin = self.client.get_admin()
        system = System(self.client, admin_resource=sys_admin)
        org = system.create_org(self.config['vcd']['org_name'],
                                self.config['vcd']['org_full_name'])
        assert org.get('name') == self.config['vcd']['org_name']

    def test_delete_org(self):
        system = System(self.client)
        system.delete_org(self.config['vcd']['org_name'], True, True)


if __name__ == '__main__':
    unittest.main()
