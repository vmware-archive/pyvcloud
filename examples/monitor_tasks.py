#! /usr/bin/env python

import json
import time, datetime, os, sys
from pyvcloud.vcloud_client import TaskStatus
from pyvcloud.vcloudair import VCA
from pyvcloud.task import Task
from pyvcloud.helper.CommonUtils import convertPythonObjToStr
import requests

from pyvcloud import vcloud_client
from lxml import etree
import sys

def ddump(r):
    print etree.tostring(r, pretty_print=True)
    print '------------------------'
    pass

vcd_uri = sys.argv[1]
user = sys.argv[2]
org = sys.argv[3]
password = sys.argv[4]

client = vcloud_client.Client(
    vcd_uri,
    api_version='27.0',
    verify_ssl_certs=False,
    log_file="simple.log",
    log_headers=True,
    log_bodies=True)

# client.set_credentials(vcloud_client.BasicLoginCredentials(user, org, password))

# admin = client.get_admin()
# ddump(admin)

# sys.exit(0)

host = sys.argv[1]
username = sys.argv[2]
org = sys.argv[3]
password = sys.argv[4]

org_url = 'https://%s/cloud' % host
verify = False
log = True
version = '27.0'
polling_interval = 5

if not verify:
    requests.packages.urllib3.disable_warnings()

vca_system = VCA(host=host, username=username, service_type='standalone', version=version, verify=verify, log=log)

result = vca_system.login(password=password, org=org, org_url=org_url)
result = vca_system.login(token=vca_system.token, org=org, org_url=vca_system.vcloud_session.org_url)
print('connected: %s' % result)

# while True:
#     print('querying pending and running tasks.')
#
#     time.sleep(polling_interval)
