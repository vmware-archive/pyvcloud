#! /usr/bin/env python

import json
import time, datetime, os, sys
from pyvcloud.vcloudair import VCA
from pyvcloud.task import Task
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

host = 'vcd.cpsbu.eng.vmware.com'
if len(sys.argv)>0:
    host = sys.argv[1]
username = 'usr1'
password = os.environ['PASSWORD']
org = 'org1'
org_url = 'https://%s/cloud' % host
verify = False
log = True
version = '27.0'

vca = VCA(host=host, username=username, service_type='standalone', version=version, verify=verify, log=log)

result = vca.login(password=password, org=org, org_url=org_url)
result = vca.login(token=vca.token, org=org, org_url=vca.vcloud_session.org_url)
print_vca(vca)

task = Task(session=vca.vcloud_session, verify=verify, log=log)
tasks = task.get_tasks()
for t in tasks.get_Task():
    print('%s, %s, %s, %s, %s, %s->%s' % (t.get_id().split(':')[-1], t.get_operation(), t.get_Owner().get_name(), t.get_status(), t.get_Progress(), str(t.get_startTime()).split('.')[0], str(t.get_endTime()).split('.')[0]))
