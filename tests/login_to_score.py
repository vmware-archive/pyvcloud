import time
import datetime
import os
from pyvcloud.vcloudair import VCA


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


def test_vcloud_session(vca, vdc, vapp):
    the_vdc = vca.get_vdc(vdc)
    for x in range(1, 1):
        print datetime.datetime.now(), the_vdc.get_name(), vca.vcloud_session.token
        the_vdc = vca.get_vdc(vdc)
        if the_vdc:
            print the_vdc.get_name(), vca.vcloud_session.token
        else:
            print False
        the_vapp = vca.get_vapp(the_vdc, vapp)
        if the_vapp:
            print the_vapp.me.name
        else:
            print False
        time.sleep(2)


# On Demand
host = 'iam.vchs.vmware.com'
username = os.environ['VCAUSER']
password = os.environ['PASSWORD']
instance = 'c40ba6b4-c158-49fb-b164-5c66f90344fa'
org = 'a6545fcb-d68a-489f-afff-2ea055104cc1'
vdc = 'VDC1'
vapp = 'ubu'

# sample login sequence on vCloud Air On Demand
vca = VCA(
    host=host,
    username=username,
    service_type='ondemand',
    version='5.7',
    verify=True)

# first login, with password
result = vca.login(password=password)
print_vca(vca)

# then login with password and instance id, this will generate a session_token
result = vca.login_to_instance(
    password=password,
    instance=instance,
    token=None,
    org_url=None)
print_vca(vca)

# next login, with token, org and org_url, no password, it will retrieve
# the organization
result = vca.login_to_instance(
    instance=instance,
    password=None,
    token=vca.vcloud_session.token,
    org_url=vca.vcloud_session.org_url)
print_vca(vca)

# this tests the vca token
result = vca.login(token=vca.token)
if result:
    print result, vca.instances
else:
    print False

# this tests the vcloud session token
test_vcloud_session(vca, vdc, vapp)

s = vca.get_score_service('https://score.vca.io')
blueprints = s.list()
for blueprint in blueprints:
    print blueprint.get('id')

s.upload('os.environ['BPFILE']', 'bp1')

blueprints = s.list()
for blueprint in blueprints:
    print blueprint.get('id')
