#!/usr/bin/env python3
# Pyvcloud Examples
#
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
#
# Illustrates how to list resources associated with org VDCs.

import sys
from pyvcloud.vcd.client import BasicLoginCredentials
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.vdc import VDC
import requests

# Collect arguments.
if len(sys.argv) != 5:
    print("Usage: python3 {0} host org user password".format(sys.argv[0]))
    sys.exit(1)
host = sys.argv[1]
org = sys.argv[2]
user = sys.argv[3]
password = sys.argv[4]

# Disable warnings from self-signed certificates.
requests.packages.urllib3.disable_warnings()

# Login. SSL certificate verification is turned off to allow self-signed
# certificates.  You should only do this in trusted environments.
print("Logging in: host={0}, org={1}, user={2}".format(host, org, user))
client = Client(host, verify_ssl_certs=False)
client.set_highest_supported_version()
client.set_credentials(BasicLoginCredentials(user, org, password))

print("Fetching Org...")
org = Org(client, resource=client.get_org())
print("Fetching VDCs...")
for vdc_info in org.list_vdcs():
    name = vdc_info['name']
    href = vdc_info['href']
    print("VDC name: {0}\n    href: {1}".format(
        vdc_info['name'], vdc_info['href']))
    vdc = VDC(client, resource=org.get_vdc(vdc_info['name']))
    print("{0}{1}".format("Name".ljust(40), "Type"))
    print("{0}{1}".format("----".ljust(40), "----"))
    for resource in vdc.list_resources():
        print('%s%s' % (resource['name'].ljust(40), resource['type']))

# Log out.
print("Logging out")
client.logout()
