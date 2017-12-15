#!/usr/bin/env python3

import os
from pyvcloud.vcd.client import BasicLoginCredentials
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.client import EntityType
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.vdc import VDC
import requests

requests.packages.urllib3.disable_warnings()

client = Client('bos1-vcd-sp-static-200-161.eng.vmware.com',
                api_version='30.0',
                verify_ssl_certs=False,
                log_file='pyvcloud.log',
                log_requests=True,
                log_headers=True,
                log_bodies=True)
client.set_credentials(BasicLoginCredentials('testuser', 'STFTestOrg',
                                             'ca$hc0w'))

org_resource = client.get_org()
org = Org(client, resource=org_resource)
vdc_resource = org.get_vdc('orgVdc-1')
vdc = VDC(client, resource=vdc_resource)
vapps = vdc.list_resources()
for vapp in vapps:
    print(vapp.get('name'))

client.logout()
