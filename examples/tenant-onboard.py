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
from pyvcloud.vcd.client import FenceMode
from pyvcloud.vcd.client import QueryResultFormat
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.system import System
from pyvcloud.vcd.utils import to_dict
from pyvcloud.vcd.vdc import VDC

# Helper functions for creating VDCs.
def _fill_in_pvdc_default(client, vdc_kwargs):
    """Convert '*' value to a default pvcd name"""
    pvdc_name = vdc_kwargs['provider_vdc_name']
    if pvdc_name == '*':
        system = System(client, admin_resource=client.get_admin())
        pvdc_refs = system.list_provider_vdcs()
        for pvdc_ref in pvdc_refs:
            pvdc_name = pvdc_ref.get('name')
            print("Defaulting to first pvdc: {0}".format(pvdc_name))
            vdc_kwargs['provider_vdc_name'] = pvdc_name
            break

        if vdc_kwargs['provider_vdc_name'] == '*':
            raise Exception("Unable to find default provider VDC")

def _fill_in_netpool_default(client, vdc_kwargs):
    """Convert '*' value to a default netpool name"""
    netpool_name = vdc_kwargs['network_pool_name']
    if netpool_name == '*':
        system = System(client, admin_resource=client.get_admin())
        netpools = system.list_network_pools()
        for netpool in netpools:
            netpool_name = netpool.get('name')
            print("Defaulting to first netpool: {0}".format(netpool_name))
            vdc_kwargs['network_pool_name'] = netpool_name
            break

        if vdc_kwargs['network_pool_name'] == '*':
            raise Exception("Unable to find default netpool")

# Collect arguments.
if len(sys.argv) != 2:
    print("Usage: python3 {0} config_file".format(sys.argv[0]))
    sys.exit(1)
config_yaml = sys.argv[1]

# Load the YAML configuration and convert to an object with properties for
# top-level entries.  Values are either scalar variables, dictionaries,
# or lists depending on the structure of the YAML.
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
client.set_credentials(BasicLoginCredentials(cfg.vcd_admin_user,
                       "System", cfg.vcd_admin_password))

# Ensure the org exists.
print("Fetching org...")
try:
    # This call gets a record that we can turn into an Org class.
    org_record = client.get_org_by_name(cfg.org)
    org = Org(client, href=org_record.get('href'))
    print("Org already exists: {0}".format(org.get_name()))
except Exception:
    print("Org does not exist, creating: {0}".format(cfg.org))
    sys_admin_resource = client.get_admin()
    system = System(client, admin_resource=sys_admin_resource)
    admin_org_resource = system.create_org(cfg.org, "Test Org", True)
    org_record = client.get_org_by_name(cfg.org)
    org = Org(client, href=org_record.get('href'))
    print("Org now exists: {0}".format(org.get_name()))

# Ensure user exists on the org.
try:
    user_resource = org.get_user(cfg.user['name'])
    print("User already exists: {0}".format(cfg.user['name']))
except Exception:
    print("User does not exist, creating: {0}".format(cfg.user['name']))
    role_record = org.get_role_record(cfg.user['role'])
    user_resource = org.create_user(user_name=cfg.user['name'],
                                    password=cfg.user['password'],
                                    role_href=role_record.get('href'))
    print("User now exists: {0}".format(user_resource.get('name')))

# Ensure the user is enabled.  We could also do so when creating the user
# but this approach will also fix an existing user who is disabled.
user_dict = to_dict(user_resource)
if user_dict.get('IsEnabled') == 'true':
    print("User is enabled: {0}".format(user_dict.get('name')))
else:
    print("User is not enabled, enabling...")
    org.update_user(user_name=user_dict.get('name'), is_enabled=True)
    print("User is now enabled: {0}".format(user_dict.get('name')))

# Ensure VDC exists.  If we create it reload the org as it affects
# org resource contents and future calls might fail otherwise.
try:
    vdc_resource = org.get_vdc(cfg.vdc['vdc_name'])
    vdc = VDC(client, resource=vdc_resource)
    print("VDC already exists: {0}".format(vdc.name))
except Exception:
    print("VDC does not exist, creating: {0}".format(cfg.vdc['vdc_name']))
    vdc_kwargs = cfg.vdc
    # Vet the netpool and pvcd arguments as either can be '*' in which 
    # case we need to find default values. 
    _fill_in_pvdc_default(client, vdc_kwargs)
    _fill_in_netpool_default(client, vdc_kwargs)
    # Now create the VDC.  
    admin_vdc_resource = org.create_org_vdc(**vdc_kwargs)
    # The 'admin_vdc_resource' is not a task but an AdminVdc entity.  Tasks
    # are two levels down.
    handle_task(client, admin_vdc_resource.Tasks.Task[0])
    org.reload()
    vdc_resource = org.get_vdc(cfg.vdc['vdc_name'])
    vdc = VDC(client, resource=vdc_resource)
    print("VDC now exists: {0}".format(vdc.name))

# Ensure the catalog exists.  For now we don't do anything special with
# permissions.  As with VDC's we reload the org if we create a catalog
# so that it's visible in future calls.
try:
    catalog_resource = org.get_catalog_resource(cfg.catalog['name'])
    print("Catalog already exists: {0}".format(cfg.catalog['name']))
except Exception:
    print("Catalog does not exist, creating: {0}".format(cfg.catalog['name']))
    catalog_kwargs = cfg.catalog
    catalog_resource = org.create_catalog(**catalog_kwargs)
    org.reload()
    print("Catalog now exists: {0}".format(catalog_resource.get('name')))

# Check for catalog_items containing OVF templates in the catalog and
# upload them if they are missing.
for catalog_item in cfg.catalog_items:
    try:
        catalog_item_resource = org.get_catalog_item(
            catalog_item['catalog_name'], catalog_item['item_name'])
        print("Catalog item exists: {0}".format(catalog_item['item_name']))
    except Exception:
        # Define a progress reporter to track upload, since it takes
        # a while.
        def progress_reporter(transferred, total):
            print("{:,} of {:,} bytes, {:.0%}".format(
                transferred, total, transferred / total))

        print("Loading catalog item: catalog={0}, item={1}, file={2}".format(
            catalog_item['catalog_name'],
            catalog_item['item_name'],
            catalog_item['file_name']))
        catalog_item['callback'] = progress_reporter
        org.upload_ovf(**catalog_item)
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
    for catalog_item in cfg.catalog_items:
        # Run a report query on this catalog item to find its state.
        catalog_item_resource = org.get_catalog_item(
            catalog_item['catalog_name'], catalog_item['item_name'])
        resource_type = 'adminCatalogItem'
        query = client.get_typed_query(
            resource_type,
            query_result_format=QueryResultFormat.ID_RECORDS,
            qfilter="catalogName=={0};name=={1}".format(
                catalog_item['catalog_name'], catalog_item['item_name']))
        item_records = list(query.execute())
        # Ensure we find the catalog item.
        if len(item_records) == 0:
            raise Exception("Catalog item not found: {0}".format(
                catalog_item['item_name']))
        else:
            for item_record in item_records:
                item_dict = to_dict(item_record, resource_type=resource_type)
                # If the template exists but is not in the right
                # state we need to wait.
                if item_dict['status'] != "RESOLVED":
                    print("Template unresolved: {0} {1} {2}".format(
                        item_dict['catalogName'],
                        item_dict['name'], item_dict['status']))
                    find_unresolved = True
                    time.sleep(3)

print("No unresolved templates found")

# Check for desired networks and create them if they don't exist.
# (We might add other kinds of networks later.)
if cfg.networks.get("isolated"):
    print("Checking isolated networks...")
    for network in cfg.networks['isolated']:
        isolated_network_list = vdc.list_orgvdc_network_resources(
            name=network['network_name'], type=FenceMode.ISOLATED.value)
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
                    name=network['network_name'],
                    type=FenceMode.ISOLATED.value)
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

