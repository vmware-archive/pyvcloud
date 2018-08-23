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
from uuid import uuid1

from pyvcloud.system_test_framework.base_test import BaseTestCase
from pyvcloud.system_test_framework.environment import CommonRoles
from pyvcloud.system_test_framework.environment import developerModeAware
from pyvcloud.system_test_framework.environment import Environment
from pyvcloud.system_test_framework.utils import \
    create_vapp_from_template

from pyvcloud.vcd.client import TaskStatus
from pyvcloud.vcd.exceptions import EntityNotFoundException

class TestVM(BaseTestCase):
    """Test vm functionalities implemented in pyvcloud."""

    _test_runner_role = CommonRoles.VAPP_AUTHOR
    _client = None

    _test_vapp_name = 'tets_vApp_' + str(uuid1())
    _test_vapp_href = None

    

    def test_0000_setup(self):
        """Setup the vms required for the other tests in this module.

        Create a vApp with just one vm as per the configuration stated above.

        This test passes if the vApp href is not None.
        """
        logger = Environment.get_default_logger()
        TestVM._client = Environment.get_client_in_default_org(
            TestVM._test_runner_role)
        vdc = Environment.get_test_vdc(TestVM._client)

        logger.debug('Creating empty vApp.')
        TestVM._test_vapp_href = create_vapp_from_template(
            client=TestVM._client,
            vdc=vdc,
            name=TestVM._test_vapp_name,
            catalog_name=Environment.get_default_catalog_name(),
            template_name=Environment.get_default_template_name())

        self.assertIsNotNone(TestVM._test_vapp_href)
