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
from pyvcloud.vcd.certificate import Certificate
from pyvcloud.vcd.crl import Crl
from pyvcloud.vcd.gateway import Gateway


class TestCertificates(BaseTestCase):
    """Test gateway certificates functionalities implemented in pyvcloud."""
    # All tests in this module should be run as System Administrator.
    _name = GatewayConstants.name
    _service_certificate_file_path = "certificate.pem"
    _ca_certificate_file_path = "certificate.pem"
    _crl_certificate_file_path = "crl.pem"
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
            service_certificate_file_path=TestCertificates.
                _service_certificate_file_path,
            private_key_file_path=TestCertificates._private_key_file_path)
        gateway_obj1.reload()
        certificates = gateway_obj1.get_certificates()
        self.__validate_certificate(certificates)

    def __validate_certificate(self, certificates):
        certificate_list = certificates.certificate
        self.assertTrue(len(certificate_list) > 0)

    def test_0015_list_service_certificate(self):
        """List all service certificates of a gateway
        Invokes the list_service_certificates of the gateway.
        """
        gateway_obj1 = TestCertificates._gateway1
        certificate_list = gateway_obj1.list_service_certificates()
        certificate = certificate_list[0]
        object_id = certificate["Object_Id"]
        TestCertificates._object_id = object_id
        # Verify
        self.assertTrue(len(certificate_list) > 0)

    def test_0020_delete_service_certificate(self):
        """Delete service certificate in the gateway.
        Invokes the delete_certificate of the Certificate.
        """
        certificate_obj = Certificate(client=TestCertificates._client,
                                      gateway_name=TestCertificates._name,
                                      resource_id=TestCertificates._object_id)
        certificate_obj.delete_certificate()
        # Verify
        gateway_obj1 = TestCertificates._gateway1
        certificate_list = gateway_obj1.list_service_certificates()
        self.assertTrue(len(certificate_list) == 0)

    def test_0025_add_ca_certificate(self):
        """Add CA certificate in the gateway.
        Invokes the add_ca_certificate of the gateway.
        """
        gateway = Environment.get_test_gateway(TestCertificates._client)
        gateway_obj1 = Gateway(TestCertificates._client, GatewayConstants.name,
                               href=gateway.get('href'))
        TestCertificates._gateway1 = gateway_obj1
        gateway_obj1.add_ca_certificate(
            ca_certificate_file_path=TestCertificates.
                _ca_certificate_file_path)
        gateway_obj1.reload()
        certificates = gateway_obj1.get_certificates()
        self.__validate_certificate(certificates)

    def test_0026_list_ca_certificate(self):
        """List CA certificates of a gateway
        Invokes the list_ca_certificates of the gateway.
        """
        gateway_obj1 = TestCertificates._gateway1
        certificate_list = gateway_obj1.list_ca_certificates()
        # Verify
        self.assertTrue(len(certificate_list) > 0)

    def test_0030_delete_ca_certificate(self):
        """Delete CA certificate in the gateway.
        Invokes the delete_ca_certificate of the Certificate.
        """
        gateway_obj1 = TestCertificates._gateway1
        certificate_list = gateway_obj1.list_ca_certificates()
        certificate = certificate_list[0]
        object_id = certificate["Object_Id"]
        certificate_obj = Certificate(client=TestCertificates._client,
                                      gateway_name=TestCertificates._name,
                                      resource_id=object_id)
        certificate_obj.delete_ca_certificate()
        # Verify
        gateway_obj1 = TestCertificates._gateway1
        certificate_list = gateway_obj1.list_ca_certificates()
        self.assertTrue(len(certificate_list) == 0)

    def test_0035_add_crl_certificate(self):
        """Add CRL certificate in the gateway.
        Invokes the add_crl_certificate of the gateway.
        """
        gateway = Environment.get_test_gateway(TestCertificates._client)
        gateway_obj1 = Gateway(TestCertificates._client, GatewayConstants.name,
                               href=gateway.get('href'))
        TestCertificates._gateway1 = gateway_obj1
        gateway_obj1.add_crl_certificate(
            crl_certificate_file_path=TestCertificates.
                _crl_certificate_file_path)
        gateway_obj1.reload()
        certificates = gateway_obj1.get_crl_certificates()
        self.__validate_crl_certificate(certificates)

    def __validate_crl_certificate(self, crls):
        certificate_list = crls.crl
        self.assertTrue(len(certificate_list) > 0)

    def test_0040_list_crl_certificate(self):
        """List crl certificates of a gateway
        Invokes the list_crl_certificates of the gateway.
        """
        gateway_obj1 = TestCertificates._gateway1
        certificate_list = gateway_obj1.list_crl_certificates()
        certificate = certificate_list[0]
        crl_object_id = certificate["Object_Id"]
        TestCertificates._crl_object_id = crl_object_id
        # Verify
        self.assertTrue(len(certificate_list) > 0)

    def test_0045_delete_crl_certificate(self):
        """Delete CRL certificate in the gateway.
        Invokes the delete_crl_certificate of the Certificate.
        """
        gateway_obj1 = TestCertificates._gateway1
        certificate_list = gateway_obj1.list_crl_certificates()
        certificate = certificate_list[0]
        object_id = certificate["Object_Id"]
        crl_obj = Crl(client=TestCertificates._client,
                      gateway_name=TestCertificates._name,
                      resource_id=object_id)
        crl_obj.delete_certificate()
        # Verify
        gateway_obj1 = TestCertificates._gateway1
        certificate_list = gateway_obj1.list_crl_certificates()
        self.assertTrue(len(certificate_list) == 0)

    def test_0098_teardown(self):
        return

    def test_0099_cleanup(self):
        """Release all resources held by this object for testing purposes."""
        TestCertificates._client.logout()

    if __name__ == '__main__':
        unittest.main()
