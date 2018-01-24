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


class TestVC(TestCase):

    def test_0001_list_vc(self):
        platform = Platform(self.client)
        vcenters = platform.list_vcenters()
        for vcenter in vcenters:
            self.logger.debug('vCenter found: %s' % vcenter.get('name'))
        assert len(vcenters) > 0

    def test_0002_get_vc(self):
        platform = Platform(self.client)
        vcenter = platform.get_vcenter(self.config['vcd']['vcenter'])
        self.logger.debug('vCenter: name=%s, url=%s' %
                          (vcenter.get('name'), vcenter.Url.text))
        assert vcenter is not None

    def test_0003_get_vc_negative(self):
        try:
            platform = Platform(self.client)
            platform.get_vcenter(self.config['vcd']['vcenter_invalid'])
            assert False
        except Exception as e:
            assert 'not found' in str(e).lower()


if __name__ == '__main__':
    unittest.main()
