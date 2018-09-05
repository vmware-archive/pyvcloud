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

from uuid import uuid1

from pyvcloud.system_test_framework.base_test import BaseTestCase
from pyvcloud.system_test_framework.environment import CommonRoles
from pyvcloud.system_test_framework.environment import developerModeAware
from pyvcloud.system_test_framework.environment import Environment

from pyvcloud.vcd.exceptions import AccessForbiddenException
from pyvcloud.vcd.exceptions import EntityNotFoundException


class TestNetwork(BaseTestCase):
    """Test network functionalities implemented in pyvcloud."""

    # Once pyvcloud is mature enough to handle external networks, directly
    # connected/routed org vdc networks, vApp networks. We will add more tests.

    _test_runner_role = CommonRoles.ORGANIZATION_ADMINISTRATOR
    _client = None
    _vapp_author_client = None

    _isolated_orgvdc_network_name = 'isolated_orgvdc_network_' + str(uuid1())
    _isolated_orgvdc_network_gateway = '10.0.0.1'
    _isolated_orgvdc_network_netmask = '255.255.255.0'

    _non_existent_isolated_orgvdc_network_name = 'non_existent_isolated_' + \
        'orgvdc_network_' + str(uuid1())

    def test_0000_setup(self):
        """Setup the networks required for the other tests in this module.

        Create an isolated org vdc network as per the configuration stated
        above.

        This test passes if the isolated orgvdc network is created
        successfully.
        """
        logger = Environment.get_default_logger()
        TestNetwork._client = Environment.get_client_in_default_org(
            TestNetwork._test_runner_role)
        TestNetwork._vapp_author_client = \
            Environment.get_client_in_default_org(CommonRoles.VAPP_AUTHOR)
        vdc = Environment.get_test_vdc(TestNetwork._client)

        logger.debug('Creating isolated orgvdc network : ' +
                     TestNetwork._isolated_orgvdc_network_name)
        result = vdc.create_isolated_vdc_network(
            network_name=TestNetwork._isolated_orgvdc_network_name,
            gateway_ip=TestNetwork._isolated_orgvdc_network_gateway,
            netmask=TestNetwork._isolated_orgvdc_network_netmask)
        TestNetwork._client.get_task_monitor().wait_for_success(
            task=result.Tasks.Task[0])

    def test_0010_list_isolated_orgvdc_networks(self):
        """Test the method vdc.list_orgvdc_isolated_networks().

        Fetches all isolated orgvdc networks in the current organization.

        This test passes if the network created during setup is present in the
        retrieved list of networks.
        """
        vdc = Environment.get_test_vdc(TestNetwork._client)
        networks = vdc.list_orgvdc_isolated_networks()
        for network in networks:
            if network.get('name') == \
               TestNetwork._isolated_orgvdc_network_name:
                return

        self.fail('Retrieved list of isolated orgvdc network doesn\'t'
                  'contain ' + TestNetwork._isolated_orgvdc_network_name)

    def test_0020_get_isolated_orgvdc_network(self):
        """Test the method vdc.get_isolated_orgvdc_network().

        Retrieve the isolated orgvdc network created during setup.

        This test passes if the network created during setup is retrieved
        successfully without any errors.
        """
        vdc = Environment.get_test_vdc(TestNetwork._client)
        network = vdc.get_isolated_orgvdc_network(
            TestNetwork._isolated_orgvdc_network_name)
        self.assertEqual(TestNetwork._isolated_orgvdc_network_name,
                         network.get('name'))

    def test_0030_get_non_existent_isolated_orgvdc_network(self):
        """Test the method vdc.get_isolated_orgvdc_network().

        This test passes if the network retrieval operation fails with a
        EntityNotFoundException.
        """
        vdc = Environment.get_test_vdc(TestNetwork._client)
        try:
            vdc.get_isolated_orgvdc_network(
                TestNetwork._non_existent_isolated_orgvdc_network_name)
            self.fail('Should not be able to fetch isolated orgvdc network ' +
                      TestNetwork._non_existent_isolated_orgvdc_network_name)
        except EntityNotFoundException as e:
            return

    def test_0040_list_isolated_orgvdc_networks_as_non_admin_user(self):
        """Test the method vdc.list_orgvdc_isolated_networks().

        Tries to fetches all isolated orgvdc networks in the current
        organization as a non admin user.

        This test passes if the operation fails with an
        AccessForbiddenException.
        """
        vdc = Environment.get_test_vdc(TestNetwork._vapp_author_client)
        try:
            result = vdc.list_orgvdc_isolated_networks()
            if len(result) > 0:
                self.fail('Should not have been able to list isolated orgvdc'
                          'networks as non admin user.')
        except AccessForbiddenException as e:
            return

    def test_0050_get_isolated_orgvdc_network_as_non_admin_user(self):
        """Test the method vdc.get_isolated_orgvdc_network().

        Tries to retrieve the isolated orgvdc network created during setup as a
        non admin user.

        This test passes if the operation fails with an
        AccessForbiddenException.
        """
        vdc = Environment.get_test_vdc(TestNetwork._vapp_author_client)
        try:
            vdc.get_isolated_orgvdc_network(
                TestNetwork._isolated_orgvdc_network_name)
            self.fail('Should not be able to fetch isolated orgvdc network ' +
                      TestNetwork._isolated_orgvdc_network_name + ' as a non' +
                      'admin user.')
        except AccessForbiddenException as e:
            return

    def test_0050_list_orgvdc_network_records_as_non_admin_user(self):
        """Test the method vdc.list_orgvdc_network_records().

        This test passes if the record of the network created during setup is
        present in the retrieved list of networks.
        """
        vdc = Environment.get_test_vdc(TestNetwork._vapp_author_client)
        records = vdc.list_orgvdc_network_records()
        for network_record in records:
            if network_record.get('name') == \
               TestNetwork._isolated_orgvdc_network_name:
                return

        self.fail('Retrieved list of orgvdc network records doesn\'t ' +
                  'contain ' + TestNetwork._isolated_orgvdc_network_name)

    def test_0060_get_orgvdc_network_record_as_non_admin_user(self):
        """Test the method vdc.get_orgvdc_network_record_by_name().

        This test passes if the record of the network created during setup is
        retrieved successfully without any errors.
        """
        vdc = Environment.get_test_vdc(TestNetwork._vapp_author_client)
        network_record = vdc.get_orgvdc_network_record_by_name(
            TestNetwork._isolated_orgvdc_network_name)
        self.assertEqual(TestNetwork._isolated_orgvdc_network_name,
                         network_record.get('name'))

    @developerModeAware
    def test_9998_teardown(self):
        """Test the method vdc.delete_isolated_orgvdc_network().

        Invoke the method for the orgvdc network created by setup.

        This test passes if the task for deleting the network succeeds.
        """
        logger = Environment.get_default_logger()
        vdc = Environment.get_test_vdc(TestNetwork._client)

        logger.debug('Deleting isolated orgvdc network : ' +
                     TestNetwork._isolated_orgvdc_network_name)
        result = vdc.delete_isolated_orgvdc_network(
            name=TestNetwork._isolated_orgvdc_network_name, force=True)
        TestNetwork._client.get_task_monitor().wait_for_success(task=result)

    def test_9999_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        if TestNetwork._client is not None:
            TestNetwork._client.logout()
        if TestNetwork._vapp_author_client is not None:
            TestNetwork._vapp_author_client.logout()
