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
from pyvcloud.system_test_framework.constants.gateway_constants import \
    GatewayConstants
from pyvcloud.vcd.gateway import Gateway


class TestCertificates(BaseTestCase):
    """Test gateway certificates functionalities implemented in pyvcloud."""

    # All tests in this module should be run as System Administrator.
    _name = GatewayConstants.name
    _service_certificate_file_path = "certificate.pem"
    _private_key_file_path = "private_key.pem"

    def test_0000_setup(self):
        TestCertificates._client = Environment.get_sys_admin_client()

    def test_0010_add_service_certificate(self):
        """Add service certificate in the gateway.

        Invokes the add_service_certificate of the gateway.
        """

        gateway = Environment.get_test_gateway(TestCertificates._client)
        gateway_obj1 = Gateway(TestCertificates._client, GatewayConstants.name,
                               href=gateway.get('href'))
        TestCertificates._gateway1 = gateway_obj1

        gateway_obj1.add_service_certificate(
            service_certificate_file_path=TestCertificates._service_certificate_file_path,
            private_key_file_path=TestCertificates._private_key_file_path)
        gateway_obj1.reload()
        certificates = gateway_obj1.get_certificates()
        self.__validate_service_certificate(certificates)

    def __validate_service_certificate(self, certificates):
        certificate_list = certificates.certificate
        self.assertTrue(len(certificate_list) > 0)

    def test_0098_teardown(self):
        return

    def test_0099_cleanup(self):
        """Release all resources held by this object for testing purposes."""

        TestCertificates._client.logout()

    if __name__ == '__main__':
        unittest.main()
