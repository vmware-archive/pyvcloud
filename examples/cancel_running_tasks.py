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
username = 'administrator'
password = os.environ['PASSWORD']
org = 'System'
org_url = 'https://%s/cloud' % host
verify = False
log = True
version = '27.0'

vca_system = VCA(host=host, username=username, service_type='standalone', version=version, verify=verify, log=log)

result = vca_system.login(password=password, org=org, org_url=org_url)
result = vca_system.login(token=vca_system.token, org=org, org_url=vca_system.vcloud_session.org_url)
print(result)

tenant_username = 'usr1'
tenant_org = 'org1'
tenant_org_url = 'https://%s/cloud/org/%s' % (host, tenant_org)

vca_tenant = VCA(host=host, username=tenant_username, service_type='standalone', version=version, verify=verify, log=log)

result = vca_tenant.login(password=password, org=tenant_org, org_url=tenant_org_url)
user_id   = vca_tenant.vcloud_session.session.get_userId().split(':')[-1]
user_name = vca_tenant.vcloud_session.username
print(user_id, user_name)
result = vca_tenant.login(token=vca_tenant.token, org=tenant_org, org_url=vca_tenant.vcloud_session.org_url)
print(result)

task_ids = []
task = Task(session=vca_tenant.vcloud_session, verify=verify, log=log)
tasks = task.get_tasks('running')
for t in tasks.get_Task():
    print('%s, %s, %s, %s, %s, %s->%s' % (t.get_id().split(':')[-1], t.get_operation(), t.get_Owner().get_name(), t.get_status(), t.get_Progress(), str(t.get_startTime()).split('.')[0], str(t.get_endTime()).split('.')[0]))
    task_ids.append(t.get_id().split(':')[-1])

# task_ids = []
# task_ids.append('b4dca9a2-ee70-4cb8-a48d-a32d80b65c05')
# task_ids.append('0333d74f-4fe6-48b4-9154-d77ae97f7870')
# task_ids.append('229e39c6-ce4e-426f-95ee-e6c7d81259c7')

task = Task(session=vca_system.vcloud_session, verify=verify, log=log)
for task_id in task_ids:
    t = task.get_task(task_id)
    if t is None:
        print('task %s not found' % task_id)
    else:
        namespace = t.get_serviceNamespace()
        operation_name = t.get_operationName()
        operation_description = t.get_operation()
        org_id   = vca_tenant.vcloud_session.organization.get_id().split(':')[-1]
        org_name = vca_tenant.vcloud_session.organization.get_name()

        print('%s, %s, %s, %s, %s, %s->%s' % (t.get_id().split(':')[-1], t.get_operation(), t.get_Owner().get_name(), t.get_status(), t.get_Progress(), str(t.get_startTime()).split('.')[0], str(t.get_endTime()).split('.')[0]))
        if t.get_status() == 'running':
            #t = task.create_or_update_task(status, namespace, operation_name, operation_description, owner_href, owner_name, owner_type, user_id, user_name, progress, task_id=task_id)
            t = task.create_or_update_task('aborted',
                                           namespace,
                                           operation_name,
                                           operation_description,
                                           t.get_Owner().get_href(),
                                           t.get_Owner().get_name(),
                                           t.get_Owner().get_type(),
                                           user_id,
                                           user_name,
                                           None,
                                           None,
                                           task_id=task_id)
            print(t)
            # print(t.get_id().split(':')[-1])
