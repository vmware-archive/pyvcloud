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

# Illustrates vCD login and how to obtain information about the installation.

import requests
import sys
from pyvcloud.vcd.client import BasicLoginCredentials
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.client import _WellKnownEndpoint

# Collect arguments.
if len(sys.argv) != 5:
    print("Usage: python3 {0} vcd_host org user password".format(sys.argv[0]))
    sys.exit(1)
vcd_host = sys.argv[1]
org = sys.argv[2]
user = sys.argv[3]
password = sys.argv[4]

# Disable warnings from self-signed certificates.
requests.packages.urllib3.disable_warnings()

# Login. SSL certificate verification is turned off to allow self-signed
# certificates.  You should only do this in trusted environments.
print("Logging in: host={0}, org={1}, user={2}".format(vcd_host, org, user))
client = Client(vcd_host,
                api_version='29.0',
                verify_ssl_certs=False,
                log_file='pyvcloud.log',
                log_requests=True,
                log_headers=True,
                log_bodies=True)
client.set_credentials(BasicLoginCredentials(user, org, password))

print("Fetching vCD installation info...")
results = client.get_resource(
    client._session_endpoints[_WellKnownEndpoint.ADMIN])
for k, v in results.items():
    print("Key: {0} Value: {1}".format(k, v))

# Log out.
print("Logging out")
client.logout()
