#!/usr/bin/env python3
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

# Example procedure to remove a tenant. This file tears down the Org specified
# in the config file supplied as an argument.  If the Org does not exist it
# does nothing.
#
# Usage: python3 tenant-remove.py tenant.yaml

from collections import namedtuple
import requests
import sys
import yaml

# Private utility functions.
from tenantlib import handle_task

from pyvcloud.vcd.client import BasicLoginCredentials
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.system import System

# Collect arguments.
if len(sys.argv) != 2:
    print("Usage: python3 {0} config_file".format(sys.argv[0]))
    sys.exit(1)
config_yaml = sys.argv[1]

# Load the YAML configuration and convert to an object with properties.
with open(config_yaml, "r") as config_file:
    config_dict = yaml.safe_load(config_file)
    cfg = namedtuple('ConfigObject', config_dict.keys())(**config_dict)

# Disable warnings from self-signed certificates.
requests.packages.urllib3.disable_warnings()

# Login. SSL certificate verification is turned off to allow self-signed
# certificates.  You should only do this in trusted environments.
print("Logging in...")
client = Client(cfg.vcd_host, verify_ssl_certs=False,
                log_file='pyvcloud.log',
                log_requests=True,
                log_headers=True,
                log_bodies=True)
client.set_highest_supported_version()
client.set_credentials(BasicLoginCredentials(cfg.vcd_admin_user, "System",
                       cfg.vcd_admin_password))

# Load the org.  If it does not exist, there's nothing to do.
print("Fetching Org...")
try:
    org_record = client.get_org_by_name(cfg.org)
except Exception:
    print("Org does not exist, nothing to be done")
    sys.exit(0)

# Delete the org.
print("Org exists, deleting: {0}".format(cfg.org))
sys_admin_resource = client.get_admin()
system = System(client, admin_resource=sys_admin_resource)
resource = system.delete_org(cfg.org, True, True)
handle_task(client, resource)
print("Deleted the org...")

# Log out.
print("All done!")
client.logout()
