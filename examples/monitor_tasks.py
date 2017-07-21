#! /usr/bin/env python

import json
import time, datetime, os, sys
from pyvcloud.vcd.vcloud_client import TaskStatus
from pyvcloud.vcd.vcloud_client import QueryResultFormat
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


def _print(r):
    root = r
    # print('%s %s %s'% (root.tag, root.attrib['id'], root.attrib['name']))
    print(root.tag)
    print(root.attrib['name'])
    print(root.attrib['status'])
    print(root.attrib['orgName'])
    if 'objectName' in root.attrib: print(root.attrib['objectName'])
    print(root.attrib['ownerName'])
    print('---')


vcd_uri = sys.argv[1]
user = sys.argv[2]
org = sys.argv[3]
password = sys.argv[4]

verify = False
log = True
version = '27.0'
polling_interval = 5

if not verify:
    requests.packages.urllib3.disable_warnings()

if vcd_uri[-1] == '/':
    vcd_uri += 'api'
else:
    vcd_uri += '/api'

client = vcloud_client.Client(
    vcd_uri,
    api_version=version,
    verify_ssl_certs=False,
    log_file="simple.log",
    log_headers=True,
    log_bodies=True)

client.set_credentials(vcloud_client.BasicLoginCredentials(user, org, password))

print(client._session.headers['x-vcloud-authorization'])

# admin = client.get_admin()
# ddump(admin)

# q = client.get_typed_query('organization')
# q = client.get_typed_query('task', query_result_format=QueryResultFormat.ID_RECORDS)
# q = client.get_typed_query('adminTask', query_result_format=QueryResultFormat.ID_RECORDS)
# q = client.get_typed_query('adminTask', equality_filter=('status', TaskStatus.RUNNING))
# q = client.get_typed_query('task', equality_filter=('name', 'CLUSTER_CREATE'))
# q = client.get_typed_query('task', equality_filter=('name', 'CLUSTER_DELETE'), query_result_format=QueryResultFormat.ID_RECORDS)
q = client.get_typed_query('adminTask', equality_filter=('status', 'running'), query_result_format=QueryResultFormat.ID_RECORDS)
qr = q.execute()
n = 0
per_org = {}
for r in qr:
    n += 1
    _print(r)
    # ddump(r)
    org = r.attrib['orgName']
    if org not in per_org.keys():
        per_org[org] = 0
    per_org[org] = per_org[org] + 1

per_org['_total'] = n
print(json.dumps(per_org))

sys.exit(0)

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
