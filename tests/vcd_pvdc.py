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

from pyvcloud.vcd.platform import Platform
from pyvcloud.vcd.test import TestCase


class TestPVDC(TestCase):
    def test_create_pvdc(self):
        platform = Platform(self.client)

        pvdc = platform.create_provider_vdc(
            vim_server_name=self.config['vcd']['vimServerName'],
            resource_pool_names=self.config['vcd']['resourcePoolNames'],
            storage_profiles=self.config['vcd']['storageProfiles'],
            pvdc_name=self.config['vcd']['pvdcName'],
            is_enabled=self.config['vcd']['isEnabled'],
            description=self.config['vcd']['description'],
            highest_hw_vers=self.config['vcd']['highestSuppHWVers'],
            nsxt_manager_name=self.config['vcd']['nsxtManager'])
        assert self.config['vcd']['pvdcName'] == pvdc.get('name')


if __name__ == '__main__':
    unittest.main()
