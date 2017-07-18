#! /usr/bin/env python

import json
import time, datetime, os, sys
from pyvcloud.vcloudair import VCA
from pyvcloud.task import Task
from pyvcloud.helper.CommonUtils import convertPythonObjToStr
import requests

host = 'vcd.vmware.com'
if len(sys.argv)>0:
    host = sys.argv[1]
username = 'administrator'
password = os.environ['PASSWORD']
org = 'System'
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

while True:
    print('querying pending and running tasks.')

    time.sleep(polling_interval)
