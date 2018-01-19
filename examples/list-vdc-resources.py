#!/usr/bin/env python3

import os
from pyvcloud.vcd.client import BasicLoginCredentials
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.vdc import VDC
import requests

requests.packages.urllib3.disable_warnings()

client = Client('bos1-vcd-sp-static-202-34.eng.vmware.com',
                verify_ssl_certs=False)
client.set_highest_supported_version()
client.set_credentials(BasicLoginCredentials('usr1', 'org1', 'ca$hc0w'))

org = Org(client, resource=client.get_org())
vdc = VDC(client, resource=org.get_vdc('vdc1'))

for resource in vdc.list_resources():
    print('%s%s' % (resource['name'].ljust(40),
                    resource['type']))

client.logout()
