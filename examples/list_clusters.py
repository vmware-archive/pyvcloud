#! /usr/bin/env python

import json
import time, datetime, os, sys
from pyvcloud.vcloudair import VCA
from pyvcloud.cluster import Cluster
from pyvcloud.helper.CommonUtils import convertPythonObjToStr

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
username = 'administrator'
password = os.environ['PASSWORD']
org = 'System'
org_url = 'https://%s/cloud' % host
verify = False
log = True
version = '27.0'

vca = VCA(host=host, username=username, service_type='standalone', version=version, verify=verify, log=log)

result = vca.login(password=password, org=org, org_url=org_url)
print_vca(vca)

cse = Cluster(session=vca.vcloud_session, verify=verify, log=log)

clusters = cse.get_clusters()
print('clusters found: %s' % len(clusters))
for cluster in clusters:
    print('cluster %s' % cluster['name'])
