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

# Example procedure to onboard a tenant. This file reads the desired org,
# user, catalog contents, network, and vapp(s) from a configuration file.
# It adds anything that is missing.  If everything already exists, the
# sample procedure does nothing.
#
# Usage: python3 tenant-onboard.py tenant.yaml

from collections import namedtuple
import requests
import sys
import time
import yaml

# Private utility functions.
from tenantlib import handle_task

from pyvcloud.vcd.client import BasicLoginCredentials
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.client import QueryResultFormat
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.system import System
from pyvcloud.vcd.utils import to_dict
from pyvcloud.vcd.vdc import VDC

# Collect arguments.
if len(sys.argv) != 2:
    print("Usage: python3 {0} config_file".format(sys.argv[0]))
    sys.exit(1)
config_yaml = sys.argv[1]

# Load the YAML configuration and convert to an object with properties for
# top-level entries.  Values are either scalar variables, dictionaries,
# or lists depending on the structure of the YAML.
with open(config_yaml, "r") as config_file:
    config_dict = yaml.load(config_file)
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
client.set_credentials(BasicLoginCredentials(cfg.vcd_admin_user,
                       "System", cfg.vcd_admin_password))

# Ensure the org exists.
print("Fetching org...")
try:
    org_resource = client.get_org_by_name(cfg.org)
    org = Org(client, resource=org_resource)
    print("Org already exists: {0}".format(org.get_name()))
except Exception:
    print("Org does not exist, creating: {0}".format(cfg.org))
    sys_admin_resource = client.get_admin()
    system = System(client, admin_resource=sys_admin_resource)
    result = system.create_org(cfg.org, "Test Org", True)
    org = Org(client, resource=client.get_org_by_name(cfg.org))
    print("Org now exists: {0}".format(org.get_name()))

# Ensure org is current.
org.reload()

# Ensure user exists on the org.
try:
    user_resource = org.get_user(cfg.user['name'])
    print("User already exists: {0}".format(cfg.user['name']))
except Exception:
    print("User does not exist, creating: {0}".format(cfg.user['name']))
    role = org.get_role_record(cfg.user['role'])
    result = org.create_user(user_name=cfg.user['name'],
                             password=cfg.user['password'],
                             role_href=role.get('href'))
    user_resource = org.get_user(cfg.user['name'])
    print("User now exists: {0}".format(cfg.user['name']))

# Ensure VDC exists.
try:
    vdc_resource = org.get_vdc(cfg.vdc['vdc_name'])
    vdc = VDC(client, resource=vdc_resource)
    print("VDC already exists: {0}".format(vdc.name))
except Exception:
    print("VDC does not exist, creating: {0}".format(cfg.vdc['vdc_name']))
    vdc_kwargs = cfg.vdc
    vdc_resource = org.create_org_vdc(**vdc_kwargs)
    # The 'vdc_resource' is not a task but an AdminVdc entity.  Tasks are two
    # levels down.  
    handle_task(client, vdc_resource.Tasks.Task[0])
    org.reload()
    vdc = VDC(client, resource=org.get_vdc(cfg.vdc['vdc_name']))
    print("VDC now exists: {0}".format(vdc.name))

# Ensure the catalog exists.  For now we don't do anything special with
# permissions.
try:
    catalog_resource = org.get_catalog_resource(cfg.catalog['name'])
    print("Catalog already exists: {0}".format(cfg.catalog['name']))
except Exception:
    print("Catalog does not exist, creating: {0}".format(cfg.catalog['name']))
    catalog_kwargs = cfg.catalog
    result = org.create_catalog(**catalog_kwargs)
    org.reload()
    catalog_resource = org.get_catalog_resource(cfg.catalog['name'])
    print("Catalog now exists: {0}".format(cfg.catalog['name']))

# Check for OVF templates in the catalog and upload them if they are missing.
for entry in cfg.templates:
    try:
        catalog_item = org.get_catalog_item(
            entry['catalog_name'], entry['item_name'])
        print("Catalog item exists: {0}".format(entry['item_name']))
    except Exception:
        # Define a progress reporter to track upload, since it takes
        # a while.
        def progress_reporter(transferred, total):
            print("{:,} of {:,} bytes, {:.0%}".format(
                transferred, total, transferred / total))

        print("Loading catalog item: catalog={0}, item={1}, file={2}".format(
            entry['catalog_name'], entry['item_name'], entry['file_name']))
        entry['callback'] = progress_reporter
        org.upload_ovf(**entry)
        print("Upload completed")

# Just because OVF templates are loaded does not mean they are usable yet.
# We check to ensure they are in the resolved state; otherwise, we cannot
# use them for vApps.  The following code loops until catalog items are
# in the right state.
print("Checking for unresolved templates")
find_unresolved = True
while find_unresolved:
    find_unresolved = False
    # Iterate over all the desired templates from the config file.
    for entry in cfg.templates:
        # Run a report query on this catalog item to find its state.
        catalog_item = org.get_catalog_item(
            entry['catalog_name'], entry['item_name'])
        resource_type = 'adminCatalogItem'
        q = client.get_typed_query(
            resource_type,
            query_result_format=QueryResultFormat.ID_RECORDS,
            qfilter="catalogName=={0};name=={1}".format(
                entry['catalog_name'], entry['item_name']))
        records = list(q.execute())
        # Ensure we find the catalog item.
        if len(records) == 0:
            raise Exception("Catalog item not found: {0}".format(
                entry['item_name']))
        else:
            for r in records:
                record = to_dict(r, resource_type=resource_type)
                # If the template exists but is not in the right
                # state we need to wait.
                if record['status'] != "RESOLVED":
                    print("Template unresolved: {0} {1} {2}".format(
                        record['catalogName'],
                        record['name'], record['status']))
                    find_unresolved = True
                    time.sleep(3)

print("No unresolved templates found")

# Check for desired networks and create them if they don't exist.
if cfg.networks.get("isolated"):
    print("Checking isolated networks...")
    for network in cfg.networks['isolated']:
        isolated_network_list = vdc.list_orgvdc_network_resources(
            name=network['network_name'], type='isolated')
        if len(isolated_network_list) > 0:
            print("Isolated network exists: {0}".format(
                network['network_name']))
        else:
            # Create the network in the vDC.
            print("Network does not exist, creating: {0}".format(
                network['network_name']))
            network_resource = vdc.create_isolated_vdc_network(**network)
            handle_task(client, network_resource.Tasks.Task[0])
            print("Network created")

            # Ensure the network is visible in the VDC.
            network_exists = False
            while not network_exists:
                new_network_list = vdc.list_orgvdc_network_resources(
                    name=network['network_name'], type='isolated')
                if len(new_network_list) > 0:
                    print("Isolated network is visible in VDC: {0}".format(
                        network['network_name']))
                    network_exists = True
                else:
                    print("Isolated network is not visible yet: {0}".format(
                        network['network_name']))
                    time.sleep(3)

# Check for vApps and create them if they don't exist.  We have to
# reload the VDC object so it has all the links to current vApps.
vdc.reload()
for vapp_cfg in cfg.vapps:
    try:
        vapp = vdc.get_vapp(vapp_cfg['name'])
        print("vApp exists: {0}".format(vapp_cfg['name']))
    except Exception:
        print("vApp does not exist: name={0}".format(vapp_cfg['name']))
        vapp_resource = vdc.instantiate_vapp(**vapp_cfg)
        print("vApp instantiated")
        # We don't track the task as instantiating a vApp takes a while.
        # Uncomment below if you want to ensure the vApps are available.
        # handle_task(client, vapp_resource.Tasks.Task[0])

# Log out.
print("All done!")
client.logout()
