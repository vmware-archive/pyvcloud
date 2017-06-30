#! /usr/bin/env python

import json
import time, datetime, os, sys
from pyvcloud.vcloudair import VCA
from pyvcloud.system import System
from pyvcloud.helper.CommonUtils import convertPythonObjToStr
from lxml import etree
import urllib

def print_vca(vca):
    if vca:
        print 'vca token:            ', vca.token
        if vca.vcloud_session:
            print 'vcloud session token: ', vca.vcloud_session.token
            print 'org name:             ', vca.vcloud_session.org
            print 'org url:              ', vca.vcloud_session.org_url
            print 'organization:         ', vca.vcloud_session.organization
        else:
            print 'vca vcloud session:   ', vca.vcloud_session
    else:
        print 'vca: ', vca

host='vcd.cpsbu.eng.vmware.com'
username = 'usr1'
password = os.environ['PASSWORD']
org = 'org1'
org_url = 'https://%s/cloud/org/org1' % host
verify = False
log = True
version = '27.0'
vdc = 'o1vdc1'
key = sys.argv[1]
value = sys.argv[2]

vca = VCA(host=host, username=username, service_type='vcd', version=version, verify=verify, log=log)

result = vca.login(password=password, org=org, org_url=org_url)
result = vca.login(token=vca.token, org=org, org_url=vca.vcloud_session.org_url)
print_vca(vca)
the_vdc = vca.get_vdc(vdc)
# query_filter = {'fields': 'metadata:cse.cluster.id', 'filter': 'metadata@:cse.cluster.id==STRING:C4'}
# query_filter = {'fields': 'metadata:cse.cluster.id', 'filter': 'metadata:cse.cluster.id==STRING:C4'}
# encoded = urllib.urlencode(query_filter)
# print(encoded)
# result = vca.query_by_metadata(encoded+'&filterEncoded=true')
# result = vca.query_by_metadata(encoded)
result = vca.query_by_metadata('fields=metadata:cse.cluster.id&filter=metadata:cse.cluster.id==STRING:C4')
# result = vca.query_by_metadata('')
print(result)
