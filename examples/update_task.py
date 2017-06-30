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

vca_system = VCA(host=host, username=username, service_type='standalone', version=version, verify=verify, log=log)

result = vca_system.login(password=password, org=org, org_url=org_url)
result = vca_system.login(token=vca_system.token, org=org, org_url=vca_system.vcloud_session.org_url)
print(result)

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
namespace = 'cpsbu.cse'
operation_name = 'create_cluster'
operation_description = 'create cluster'
org_id   = vca_tenant.vcloud_session.organization.get_id().split(':')[-1]
org_name = vca_tenant.vcloud_session.organization.get_name()
owner_href = 'urn:cse:cluster:77a8c02f-643c-4ba4-9517-f93f08932422'
owner_name = 'cluster-77a8c02f'
owner_type = 'application/cpsbu.cse.cluster+xml'
progress       = int(sys.argv[3])
status         = sys.argv[2]
task_id        = sys.argv[1]

print(status, namespace, operation_name, operation_description, owner_href, owner_name, owner_type, user_id, user_name, progress, task_id)

task = Task(session=vca_system.vcloud_session, verify=verify, log=log)
t = task.create_or_update_task(status, namespace, operation_name, operation_description, owner_href, owner_name, owner_type, user_id, user_name, progress, task_id=task_id)
print(t.get_id().split(':')[-1])
