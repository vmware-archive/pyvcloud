#! /usr/bin/env python

import json
import time, datetime, os, sys
from pyvcloud.vcloudair import VCA
from pyvcloud.task import Task
from pyvcloud.helper.CommonUtils import convertPythonObjToStr
from fabric.api import env, run, execute
from fabric import network
from fabric.context_managers import settings

def host_type():
    result = run('uname -a')
    return result

def wait_for_task(task, task_id):
    t = task.get_task(task_id)
    while t.get_status() != 'success':
        time.sleep(3)
        t = task.get_task(task_id)
        print('%s, %s, %s, %s, %s, %s->%s' % (t.get_id().split(':')[-1], t.get_operation(), t.get_Owner().get_name(), t.get_status(), t.get_Progress(), str(t.get_startTime()).split('.')[0], str(t.get_endTime()).split('.')[0]))

host='vcd.cpsbu.eng.vmware.com'   #cpsbu
username = 'administrator'
password = os.environ['PASSWORD']
org = 'org1'
org_url = 'https://%s/cloud' % host
verify = False
log = True
version = '27.0'

tenant_username = 'usr1'
tenant_org = 'org1'
tenant_org_url = 'https://%s/cloud/org/%s' % (host, tenant_org)
tenant_vdc = 'o1vdc1'
network = 'odnet4'
mode = 'pool'

vm_name = sys.argv[1]
root_password = sys.argv[2]

vca_tenant = VCA(host=host, username=tenant_username, service_type='standalone', version=version, verify=verify, log=log)

result = vca_tenant.login(password=password, org=tenant_org, org_url=tenant_org_url)
assert(result)
user_id   = vca_tenant.vcloud_session.session.get_userId().split(':')[-1]
user_name = vca_tenant.vcloud_session.username
result = vca_tenant.login(token=vca_tenant.token, org=tenant_org, org_url=vca_tenant.vcloud_session.org_url)
assert(result)
task = Task(session=vca_tenant.vcloud_session, verify=verify, log=log)
assert(task)

catalog = 'mycatalog'
template = 'kube.ova'

t = vca_tenant.create_vapp(tenant_vdc, vm_name, template, catalog, vm_name=vm_name)
assert(t)
task_id = t.get_id().split(':')[-1]
wait_for_task(task, task_id)

the_vdc = vca_tenant.get_vdc(tenant_vdc)
assert(the_vdc)
the_vapp = vca_tenant.get_vapp(the_vdc, vm_name)
assert(the_vapp)

t = the_vapp.disconnect_vms()
assert(t)
task_id = t.get_id().split(':')[-1]
wait_for_task(task, task_id)

t = the_vapp.disconnect_from_networks()
assert(t)
task_id = t.get_id().split(':')[-1]
wait_for_task(task, task_id)

nets = filter(lambda n: n.name == network,
              vca_tenant.get_networks(tenant_vdc))
assert(len(nets)==1)
print("connecting vApp to network"
                    " '%s' with mode '%s'" %
                    (network, mode))
t = the_vapp.connect_to_network(
    nets[0].name, nets[0].href)
assert(t)
task_id = t.get_id().split(':')[-1]
wait_for_task(task, task_id)

t = the_vapp.connect_vms(
    nets[0].name,
    connection_index=0,
    ip_allocation_mode=mode.upper(),
    mac_address=None, ip_address='')
assert(t)
task_id = t.get_id().split(':')[-1]
wait_for_task(task, task_id)

the_vapp = vca_tenant.get_vapp(the_vdc, vm_name)
assert(the_vapp)
main_ip = ''
for vm in the_vapp.me.Children.Vm:
    sections = vm.get_Section()
    virtualHardwareSection = (
        filter(lambda section:
               section.__class__.__name__ ==
               "VirtualHardwareSection_Type",
               sections)[0])
    items = virtualHardwareSection.get_Item()
    _url = '{http://www.vmware.com/vcloud/v1.5}ipAddress'
    for item in items:
        if item.Connection:
            for c in item.Connection:
                if c.anyAttributes_.get(_url):
                    main_ip = c.anyAttributes_.get(_url)
print('main_ip=%s' % main_ip)
assert(main_ip != '')

cust_script = """
#!/bin/bash
echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDNwNmuPOdoeLuACweWbWcepGdSXdloxzfGMaiBGZbZ+YLkDwq23dfEv1IzVmajrlUukpu/mnIl6JQcK7rlVnVCp2bXCoGho65DMrQdj7q212p041gIJK5DFLUlq9tijBmj5eSxdUuOs+FpS1QCkBx6ugJCBmFb86TBO5T291VVUOMIVsTH9BuAhI5RQmBHuiHgxZ/XyCojAuC6P88ulpNQcMlS9HQSljkHlUU/is5TKDhCbKRetrZ1ZPIWtz47J7zgeL8elExY9wznURWEKmE6tgdyDNTnqWeiDztLNz2cxrukYP8QhZXDGJxmDKvWgGVXPoNcQR4Se4exFB2due+33pLetojKKz9GqM/+WZHKrFJ2kW24Tb5k18eTLX1fPeqhosaOKQJPseGiJiz4vjdJa6XuqIGVLKFgeT87uUBbgvu3FcTj/rtuTDiDX0eYUakDlnzJ4D/mzV2sb2//UHy24uZNb04UZsj8uF63aPgBVR4NG1d8Nm8DxREi9CEAVrdKIebprQJYQWxhGeJNarOHVYa2P2+5Y7CRN3qirnpv//AHR6Pcp3Nw/bsUcExCz5jcy8cL2+lacsUN9OnkKckEMP2jsjQLd1m68dPNUwG1lsT6Y8hrDn/4Pn6b2meB+w+XjfjYHPI+uNs74ayL8dGX7+fghMOwA2ne94fuePY4hQ== pgomez@vmware.com' > /root/.ssh/authorized_keys
temp="%s"
echo -e "$temp\n$temp" | passwd root
chage -I -1 -m 0 -M -1 -E -1 root
cat >/etc/pam.d/vmtoolsd << EOF
auth            include         system-auth
account         include         system-account
password        include         system-password
session         include         system-session
EOF
""" % root_password

print(cust_script)

t = the_vapp.customize_guest_os(vm_name, cust_script,
        computer_name=vm_name,
        admin_password=root_password,
        reset_password_required=False)
assert(t)
task_id = t.get_id().split(':')[-1]
wait_for_task(task, task_id)

t = the_vapp.force_customization(vm_name)
task_id = t.get_id().split(':')[-1]
wait_for_task(task, task_id)

t = the_vapp.poweron()
assert(t)
task_id = t.get_id().split(':')[-1]
wait_for_task(task, task_id)

env.user = 'root'
env.key_filename = '~/.ssh/id_rsa_vmw'
env.timetout = 10
env.connection_attempts = 12
env.hosts = [main_ip]
host_types = execute(host_type)
print(host_types)
