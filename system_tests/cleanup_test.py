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

from pyvcloud.system_test_framework.base_test import BaseTestCase
from pyvcloud.system_test_framework.environment import Environment

from pyvcloud.vcd.client import TaskStatus
from pyvcloud.vcd.system import System


class TestCleanup(BaseTestCase):
    """Special test to clean up the test environment.

    Usually run after a successful test run.
    """

    def test_cleanup(self):
        """Get the test Org and delete it."""
        client = None
        try:
            logger = Environment.get_default_logger()
            client = Environment.get_sys_admin_client()
            test_org = Environment.get_test_org(client)

            logger.debug('Deleting test org: {0}'.format(test_org.get_name()))
            sys_admin_resource = client.get_admin()
            system = System(client, admin_resource=sys_admin_resource)
            task = system.delete_org(test_org.get_name(), True, True)

            # Track the task to completion.
            result = client.get_task_monitor().wait_for_success(task)
            self.assertEqual(result.get('status'), TaskStatus.SUCCESS.value)
        finally:
            if client is not None:
                client.logout()


if __name__ == '__main__':
    unittest.main()
