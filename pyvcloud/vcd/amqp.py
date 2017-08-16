# VMware vCloud Director Python SDK
# Copyright (c) 2014 VMware, Inc. All Rights Reserved.
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

from lxml import objectify
from pyvcloud.vcd.client import _WellKnownEndpoint
from pyvcloud.vcd.client import EntityType


Amqp = objectify.ElementMaker(
    annotate=False,
    namespace='http://www.vmware.com/vcloud/extension/v1.5',
    nsmap={None: "http://www.vmware.com/vcloud/v1.5",
           'vmext': 'http://www.vmware.com/vcloud/extension/v1.5'})


class AmqpService(object):

    def __init__(self, client):
        self.client = client
        if _WellKnownEndpoint.EXTENSION not in client._session_endpoints:
            raise Exception("Requires login as 'system administrator'.")
        self.endpoint = \
            client._session_endpoints[_WellKnownEndpoint.EXTENSION] + \
            '/settings/amqp'

    def get_settings(self):
        return self.client.get_resource(self.endpoint)

    def _to_settings(self, config, password):
        settings = Amqp.AmqpSettings()
        settings.append(Amqp.AmqpHost(config['AmqpHost']))
        settings.append(Amqp.AmqpPort(config['AmqpPort']))
        settings.append(Amqp.AmqpUsername(config['AmqpUsername']))
        settings.append(Amqp.AmqpPassword(password))
        settings.append(Amqp.AmqpExchange(config['AmqpExchange']))
        settings.append(Amqp.AmqpVHost(config['AmqpVHost']))
        settings.append(Amqp.AmqpUseSSL(config['AmqpUseSSL']))
        settings.append(Amqp.AmqpSslAcceptAll(config['AmqpSslAcceptAll']))
        settings.append(Amqp.AmqpPrefix(config['AmqpPrefix']))
        return settings

    def test_config(self, config, password):
        return self.client.post_resource(
            self.endpoint + '/action/test',
            self._to_settings(config, password),
            EntityType.AMQP_SETTINGS.value)

    def set_config(self, config, password):
        return self.client.put_resource(
            self.endpoint,
            self._to_settings(config, password),
            EntityType.AMQP_SETTINGS.value)
