#! /usr/bin/env python

import json
import time, datetime, os, sys
from pyvcloud.vcloudair import VCA
from pyvcloud.task import Task
from pyvcloud.helper.CommonUtils import convertPythonObjToStr

host='vcd.cpsbu.eng.vmware.com'
username = 'administrator'
password = os.environ['PASSWORD']
org = 'System'
org_url = 'https://%s/cloud' % host
verify = False
log = True
version = '27.0'

tenant_username = 'usr1'
tenant_org = 'org1'
tenant_org_url = 'https://%s/cloud/org/%s' % (host, tenant_org)

vca_tenant = VCA(host=host, username=tenant_username, service_type='standalone', version=version, verify=verify, log=log)

result = vca_tenant.login(password=password, org=tenant_org, org_url=tenant_org_url)
print(result)
user_id   = vca_tenant.vcloud_session.session.get_userId().split(':')[-1]
user_name = vca_tenant.vcloud_session.username
result = vca_tenant.login(token=vca_tenant.token, org=tenant_org, org_url=vca_tenant.vcloud_session.org_url)
print(result)
task_id = sys.argv[1]

task = Task(session=vca_tenant.vcloud_session, verify=verify, log=log)
t = task.get_task(task_id)
if t is None:
    print('task %s not found' % task_id)
else:
    print('%s, %s, %s, %s, %s, %s->%s' % (t.get_id().split(':')[-1], t.get_operation(), t.get_Owner().get_name(), t.get_status(), t.get_Progress(), str(t.get_startTime()).split('.')[0], str(t.get_endTime()).split('.')[0]))
