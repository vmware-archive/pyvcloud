# VMware vCloud Director Python SDK
# Copyright (c) 2014-2017 VMware, Inc. All Rights Reserved.
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

from pyvcloud.vcd.client import _WellKnownEndpoint
from pyvcloud.vcd.client import E_VMEXT
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.exceptions import ClientException


class AmqpService(object):
    def __init__(self, client):
        """Constructor for AmqpService object.

        :param pyvcloud.vcd.client.Client client: the client that will be used
            to make REST calls to vCD.
        """
        self.client = client
        if _WellKnownEndpoint.EXTENSION not in client._session_endpoints:
            raise ClientException("Requires login as 'system administrator'.")
        self.href = \
            client._session_endpoints[_WellKnownEndpoint.EXTENSION] + \
            '/settings/amqp'

    def get_settings(self):
        """Fetches the XML representation of the AMQP service setting.

        :return: an object containing EntityType.AMQP_SETTINGS XML data.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        return self.client.get_resource(self.href)

    def _to_settings(self, config, password):
        """Converts dictionary representation of configuration to XML element.

        :param dict config: dictionary representation of AMQP service
            configuration.
        :param str password: password of the user for the AMQP service.

        :return: an object containing EntityType.AMQP_SETTINGS XML data
            representing the configuration of the AMQP service.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        settings = E_VMEXT.AmqpSettings()
        settings.append(E_VMEXT.AmqpHost(config['AmqpHost']))
        settings.append(E_VMEXT.AmqpPort(config['AmqpPort']))
        settings.append(E_VMEXT.AmqpUsername(config['AmqpUsername']))
        settings.append(E_VMEXT.AmqpPassword(password))
        settings.append(E_VMEXT.AmqpExchange(config['AmqpExchange']))
        settings.append(E_VMEXT.AmqpVHost(config['AmqpVHost']))
        settings.append(E_VMEXT.AmqpUseSSL(config['AmqpUseSSL']))
        settings.append(E_VMEXT.AmqpSslAcceptAll(config['AmqpSslAcceptAll']))
        settings.append(E_VMEXT.AmqpPrefix(config['AmqpPrefix']))
        return settings

    def test_config(self, config, password):
        """Tests the validity of configuration on the AMQP service.

        :param dict config: dictionary representation of AMQP service
            configuration.
        :param str password: password of the user for the AMQP service.

        :return: an object containing vmext:AmqpSettingsTest XML element
            representing the result of the test performed on the AMQP service.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        return self.client.post_resource(self.href + '/action/test',
                                         self._to_settings(config, password),
                                         EntityType.AMQP_SETTINGS.value)

    def set_config(self, config, password):
        """Updates the configuration of the AMQP service.

        :param dict config: dictionary representation of AMQP service
            configuration.
        :param str password: password of the user for the amqp service.

        :return: an object containing EntityType.AMQP_SETTINGS XML data
            representing the configuration of the AMQP service.

        :rtype: lxml.objectify.ObjectifiedElement
        """
        return self.client.put_resource(self.href,
                                        self._to_settings(config, password),
                                        EntityType.AMQP_SETTINGS.value)
