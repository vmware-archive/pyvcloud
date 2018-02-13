# VMware vCloud Director Python SDK
# Copyright (c) 2017-2018 VMware, Inc. All Rights Reserved.
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

from pyvcloud.vcd.api_extension import APIExtension
from pyvcloud.vcd.test import TestCase


class TestExtension(TestCase):

    def test_0001_create_extension(self):
        extension = APIExtension(self.client)
        extension.add_extension(self.config['vcd']['extension_name'],
                                self.config['vcd']['extension_namespace'],
                                self.config['vcd']['routing_key'],
                                self.config['vcd']['exchange'],
                                self.config['vcd']['patterns'].split(','))

    def test_0002_get_extension(self):
        extension = APIExtension(self.client)
        ext_info = extension.get_extension_info(
            self.config['vcd']['extension_name'],
            self.config['vcd']['extension_namespace'])
        assert ext_info
        assert ext_info['name'] == self.config['vcd']['extension_name']
        assert ext_info['namespace'] == \
            self.config['vcd']['extension_namespace']
        assert ext_info['filter_1'].startswith('/api/')

    def test_0003_delete_extension(self):
        extension = APIExtension(self.client)
        extension.delete_extension(self.config['vcd']['extension_name'],
                                   self.config['vcd']['extension_namespace'])


if __name__ == '__main__':
    unittest.main()
