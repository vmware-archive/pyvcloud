# VMware vCloud Director Python SDK
# Copyright (c) 2014-2018 VMware, Inc. All Rights Reserved.
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

from pyvcloud.vcd.org import Org
from pyvcloud.vcd.test import TestCase
from pyvcloud.vcd.vdc import VDC


class TestStorageProfile(TestCase):
    def test_010_get_storage_profiles(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=vdc_resource)

        profiles = vdc.get_storage_profiles()

        assert len(profiles) > 0

    def test_020_get_storage_profile_by_name(self):
        logged_in_org = self.client.get_org()
        org = Org(self.client, resource=logged_in_org)
        vdc_resource = org.get_vdc(self.config['vcd']['vdc'])
        vdc = VDC(self.client, resource=vdc_resource)

        profile = vdc.get_storage_profile(
            self.config['vcd']['storage_profile_1_name'])

        assert profile.get('name') == \
            self.config['vcd']['storage_profile_1_name']


if __name__ == '__main__':
    unittest.main()
