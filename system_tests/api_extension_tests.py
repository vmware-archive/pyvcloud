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
from pyvcloud.system_test_framework.environment import developerModeAware
from pyvcloud.system_test_framework.environment import Environment

from pyvcloud.vcd.api_extension import APIExtension
from pyvcloud.vcd.exceptions import MissingRecordException
from pyvcloud.vcd.exceptions import MultipleRecordsException


class TestApiExtension(BaseTestCase):
    """Test vCD api extension feature implemented in pyvcloud."""

    # All tests in this module should be run as System Administrator
    _client = None
    _service1_href = None
    _service2_href = None

    _service_name = 'service' + str(uuid1())
    _service1_namespace = 'namespace1_' + str(uuid1())
    _service2_namespace = 'namespace2_' + str(uuid1())
    _service_routing_key = 'key_' + str(uuid1())
    _service_exchange = 'exchange_' + str(uuid1())
    _service_patterns = ['/api/bogus1', '/api/bogus2', '/api/bogus3']

    _right_name = 'right_' + str(uuid1())
    _category = 'category_' + str(uuid1())
    _description = 'description_' + str(uuid1())
    _bundle_key = 'bundlekey_' + str(uuid1())

    _non_existent_service_name = '_non_existent_service_' + str(uuid1())
    _non_existent_service_namespace = '_non_existent_namespace_' + str(uuid1())

    def test_0000_setup(self):
        """Setup an api extension service required by the other tests.

        Register two services as per the configuration stated above. Tests
        APIExtension.add_extension() method.

        This test passes if service hrefs are not None.
        """
        logger = Environment.get_default_logger()
        TestApiExtension._client = Environment.get_sys_admin_client()
        api_extension = APIExtension(TestApiExtension._client)

        # Create two services with same name but diffent namespaces
        logger.debug('Registering service (name:' +
                     TestApiExtension._service_name + ', namespace:' +
                     TestApiExtension._service1_namespace + ').')
        registered_extension = api_extension.add_extension(
            name=TestApiExtension._service_name,
            namespace=TestApiExtension._service1_namespace,
            routing_key=TestApiExtension._service_routing_key,
            exchange=TestApiExtension._service_exchange,
            patterns=TestApiExtension._service_patterns)

        TestApiExtension._service1_href = registered_extension.get('href')
        self.assertIsNotNone(TestApiExtension._service1_href)

        logger.debug('Registering service (name:' +
                     TestApiExtension._service_name + ', namespace:' +
                     TestApiExtension._service2_namespace + ').')
        registered_extension = api_extension.add_extension(
            name=TestApiExtension._service_name,
            namespace=TestApiExtension._service2_namespace,
            routing_key=TestApiExtension._service_routing_key,
            exchange=TestApiExtension._service_exchange,
            patterns=TestApiExtension._service_patterns)

        TestApiExtension._service2_href = registered_extension.get('href')
        self.assertIsNotNone(TestApiExtension._service2_href)

    def _check_service_details(self, service, expected_namespace):
        self.assertIsNotNone(service)
        self.assertEqual(service['name'], TestApiExtension._service_name)
        self.assertEqual(service['namespace'], expected_namespace)
        self.assertEqual(service['routingKey'],
                         TestApiExtension._service_routing_key)
        self.assertEqual(service['exchange'],
                         TestApiExtension._service_exchange)

    def _check_filter_details(self, service):
        expected_filter_patterns = TestApiExtension._service_patterns
        for i in range(1, len(expected_filter_patterns) + 1):
            self.assertIn(service['filter_' + str(i)],
                          expected_filter_patterns)

    def test_0010_list_service(self):
        """Test the method APIExtension.list_extensions().

        This test passes if the a list of dictionary of size >= 2 is returned
        by the method. And the dictionary contains information about the
        service registered during setup.
        """
        api_extension = APIExtension(TestApiExtension._client)
        service_list = api_extension.list_extensions()
        self.assertTrue(len(service_list) >= 2)

        count_expected_services = 2
        count_found_services = 0
        for service in service_list:
            if service['name'] == TestApiExtension._service_name:
                if service['namespace'] == \
                        TestApiExtension._service1_namespace:
                    self._check_service_details(
                        service,
                        TestApiExtension._service1_namespace)
                    count_found_services += 1
                if service['namespace'] == \
                        TestApiExtension._service2_namespace:
                    self._check_service_details(
                        service,
                        TestApiExtension._service2_namespace)
                    count_found_services += 1
        self.assertEqual(count_found_services, count_expected_services)

    def test_0020_get_service_info(self):
        """Test the method APIExtension.get_extension_info().

        Invoke the method with the name and namespace of the first service
        created in setup. A call to APIExtension.get_extension_info() also
        tests APIExtension.get_extension() and APIExtension.get_api_filters().

        This test passes if the service detail retrieved by the method is
        not None, and the details are correct.
        """
        api_extension = APIExtension(TestApiExtension._client)
        service = api_extension.get_extension_info(
            name=TestApiExtension._service_name,
            namespace=TestApiExtension._service1_namespace)
        self._check_service_details(service,
                                    TestApiExtension._service1_namespace)
        self._check_filter_details(service)

    def test_0030_get_service_info_with_invalid_name(self):
        """Test the method APIExtension.get_extension_info().

        Invoke the method with an invalid service name.

        This test passes if the an MissingRecordException is raised by the
        method.
        """
        api_extension = APIExtension(TestApiExtension._client)
        try:
            api_extension.get_extension_info(
                name=TestApiExtension._non_existent_service_name)
            self.fail('Should not be able to fetch service ' +
                      TestApiExtension._non_existent_service_name)
        except MissingRecordException as e:
            pass

    def test_0040_get_service_info_with_no_namespace(self):
        """Test the method APIExtension.get_extension_info().

        Invoke the method with the name of the first service created in setup,
        but don't send the namespace.

        This test passes if the an MultipleRecordsException is raised by the
        method.
        """
        api_extension = APIExtension(TestApiExtension._client)
        try:
            api_extension.get_extension_info(
                name=TestApiExtension._service_name)
            self.fail('Should not be able to fetch service ' +
                      TestApiExtension._service_name +
                      ' with an empty namespace.')
        except MultipleRecordsException as e:
            pass

    def test_0050_get_service_info_with_invalid_namespace(self):
        """Test the method APIExtension.get_extension_info().

        Invoke the method with the name of the service created in setup, but an
        invalid namespace.

        This test passes if the an empty dictionary is returned by the method.
        """
        api_extension = APIExtension(TestApiExtension._client)
        try:
            api_extension.get_extension_info(
                name=TestApiExtension._service_name,
                namespace=TestApiExtension._non_existent_service_namespace)
            self.fail('Should not be able to fetch service ' +
                      TestApiExtension._non_existent_service_name)
        except MissingRecordException as e:
            pass

    def test_0060_enable_disable_service(self):
        """Test the method APIExtension.enable_extension().

        This test passes if the href returned after each execution of the
        method matches the service href.
        """
        logger = Environment.get_default_logger()
        api_extension = APIExtension(TestApiExtension._client)

        logger.debug('Disabling service (name:' +
                     TestApiExtension._service_name + ', namespace:' +
                     TestApiExtension._service1_namespace + ').')
        href = api_extension.enable_extension(
            name=TestApiExtension._service_name,
            namespace=TestApiExtension._service1_namespace,
            enabled=False)
        self.assertEqual(href, TestApiExtension._service1_href)

        logger.debug('Re-enabling service (name:' +
                     TestApiExtension._service_name + ', namespace:' +
                     TestApiExtension._service1_namespace + ').')
        href = api_extension.enable_extension(
            name=TestApiExtension._service_name,
            namespace=TestApiExtension._service1_namespace,
            enabled=True)
        self.assertEqual(href, TestApiExtension._service1_href)

    def test_007_register_service_right(self):
        """Test the method APIExtension.add_service_right().

        This test passes if the right-name returned after execution of the
        method matches the expected right-name.
        """
        logger = Environment.get_default_logger()
        api_extension = APIExtension(TestApiExtension._client)

        # Create a new right for CSE RBAC
        logger.debug('Registering service right(name:' +
                     TestApiExtension._right_name + ', description:' +
                     TestApiExtension._description + ', category:' +
                     TestApiExtension._category + ').')
        register_right = api_extension.add_service_right(
            right_name=TestApiExtension._right_name,
            service_name=TestApiExtension._service_name,
            namespace=TestApiExtension._service1_namespace,
            description=TestApiExtension._description,
            category=TestApiExtension._category,
            bundle_key=TestApiExtension._bundle_key)

        expected_right_name = '{' + TestApiExtension._service1_namespace +\
                              '}:' + TestApiExtension._right_name
        registered_right_name = register_right.get('name')
        self.assertEqual(expected_right_name, registered_right_name)

    def test_0080_update_service(self):
        """Test the method APIExtension.update_extension().

        This test passes if the routing key and exchange after execution of the
        method matches the respective test strings.
        """
        logger = Environment.get_default_logger()
        api_extension = APIExtension(TestApiExtension._client)
        ext_name = TestApiExtension._service_name
        ext_namespace = TestApiExtension._service1_namespace

        logger.debug('Updating service (name:' +
                     ext_name + ', namespace:' +
                     ext_namespace + ').')

        test_routing_key = 'testroutingkey'
        test_exchange = 'testexchange'
        href = api_extension.update_extension(
            name=ext_name,
            namespace=ext_namespace,
            routing_key=test_routing_key,
            exchange=test_exchange)
        self.assertEqual(href, TestApiExtension._service1_href)

        ext_info = api_extension.get_extension_info(ext_name,
                                                    namespace=ext_namespace)
        self.assertEqual(ext_info['routingKey'], test_routing_key)
        self.assertEqual(ext_info['exchange'], test_exchange)

    @developerModeAware
    def test_9998_teardown(self):
        """Test the method APIExtension.delete_extension().

        Invoke the method for the service created during setup.

        This test passes if no errors are generated while deleting the service.
        """
        logger = Environment.get_default_logger()
        api_extension = APIExtension(TestApiExtension._client)

        logger.debug('Deleting service (name:' +
                     TestApiExtension._service_name + ', namespace:' +
                     TestApiExtension._service1_namespace + ').')
        api_extension.delete_extension(
            name=TestApiExtension._service_name,
            namespace=TestApiExtension._service1_namespace)

        logger.debug('Deleting service (name:' +
                     TestApiExtension._service_name + ', namespace:' +
                     TestApiExtension._service1_namespace + ').')
        api_extension.delete_extension(
            name=TestApiExtension._service_name,
            namespace=TestApiExtension._service2_namespace)

    def test_9999_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestApiExtension._client.logout()
