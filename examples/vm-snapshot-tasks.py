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
# Illustrates how to create, revert and remove snapshot from the VM in vApp.
#

import sys
from pyvcloud.vcd.client import BasicLoginCredentials
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.vdc import VDC
from pyvcloud.vcd.vapp import VApp
from pyvcloud.vcd.vm import VM
import requests

# Collect arguments.
if len(sys.argv) != 8:
    print("Usage: python3 {0} host org user password vdc".format(sys.argv[0]))
    sys.exit(1)
host = sys.argv[1]
org = sys.argv[2]
user = sys.argv[3]
password = sys.argv[4]
vdc = sys.argv[5]
vapp = sys.argv[6]
vm = sys.argv[7]

# Disable warnings from self-signed certificates.
requests.packages.urllib3.disable_warnings()

# Login. SSL certificate verification is turned off to allow self-signed
# certificates.  You should only do this in trusted environments.
print("Logging in: host={0}, org={1}, user={2}".format(host, org, user))
client = Client(host,
                api_version='27.0',
                verify_ssl_certs=False,
                log_file='pyvcloud.log',
                log_requests=True,
                log_headers=True,
                log_bodies=True)
client.set_credentials(BasicLoginCredentials(user, org, password))
task_monitor = client.get_task_monitor()

print("Fetching Org...")
org_resource = client.get_org()
org = Org(client, resource=org_resource)

print("Fetching VDC...")
vdc_resource = org.get_vdc(vdc)
vdc = VDC(client, resource=vdc_resource)

print("Fetching vApp...")
vapp_resource = vdc.get_vapp(vapp)
vapp = VApp(client, resource=vapp_resource)

print("Fetching VM...")
vm_resource = vapp.get_vm(vm)
vm = VM(client, resource=vm_resource)

print("Creating Snapshot...")
snaphot_resource = vm.snapshot_create(memory=False, quiesce=False)
print("Waiting for Snapshot finish...")
task_monitor.wait_for_success(snaphot_resource)

print("Revert Back To Current Snapshot...")
vm.reload()
snaphot_resource = vm.snapshot_revert_to_current()
print("Waiting for Revert finish...")
task_monitor.wait_for_success(snaphot_resource)

print("Remove All Snapshot...")
snaphot_resource = vm.snapshot_remove_all()
print("Waiting for Revert finish...")
task_monitor.wait_for_success(snaphot_resource)

# Log out.
print("Logging out")
client.logout()
