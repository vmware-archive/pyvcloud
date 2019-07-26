# VMware vCloud Director Python SDK
# Copyright (c) 2014-2019 VMware, Inc. All Rights Reserved.
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
from pyvcloud.system_test_framework.base_test import BaseTestCase
from pyvcloud.system_test_framework.environment import Environment

from pyvcloud.vcd.platform import Platform

class TestDatastore(BaseTestCase):
    """Test datastore functionalities implemented in pyvcloud."""
    # All tests in this module should be run as System Administrator.

    def test_0000_setup(self):
        TestDatastore._client = Environment.get_sys_admin_client()

    def test_0015_list_datastores(self):
        """List all datastores
        Invokes the list_datastores of the platform.
        """
        platform = Platform(client=TestDatastore._client)
        datastore_list = platform.list_datastores()
        # Verify
        self.assertTrue(len(datastore_list) > 0)

    def test_0098_teardown(self):
        return

    def test_0099_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestDatastore._client.logout()

    if __name__ == '__main__':
        unittest.main()
