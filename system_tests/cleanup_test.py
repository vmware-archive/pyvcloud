# Copyright (c) 2018 VMware, Inc. All Rights Reserved.
#
# This product is licensed to you under the
# Apache License, Version 2.0 (the "License").
# You may not use this product except in compliance with the License.
#
# This product may include a number of subcomponents with
# separate copyright notices and license terms. Your use of the source
# code for the these subcomponents is subject to the terms and
# conditions of the subcomponent's license, as noted in the LICENSE file.

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
