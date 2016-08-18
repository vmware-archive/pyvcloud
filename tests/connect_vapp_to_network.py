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

# On Demand
host = 'iam.vchs.vmware.com'
username = os.environ['VCAUSER']
password = os.environ['PASSWORD']
instance = 'c40ba6b4-c158-49fb-b164-5c66f90344fa'
org = 'a6545fcb-d68a-489f-afff-2ea055104cc1'
vdc = 'VDC1'
vapp = 'ubu'
network = 'default-routed-network'

vca = VCA(
    host=host,
    username=username,
    service_type='ondemand',
    version='5.7',
    verify=True)
assert vca
result = vca.login(password=password)
assert result
result = vca.login_to_instance(
    password=password,
    instance=instance,
    token=None,
    org_url=None)
assert result
result = vca.login_to_instance(
    instance=instance,
    password=None,
    token=vca.vcloud_session.token,
    org_url=vca.vcloud_session.org_url)
assert result
print_vca(vca)

the_vdc = vca.get_vdc(vdc)
assert the_vdc
print the_vdc.get_name()
the_vapp = vca.get_vapp(the_vdc, vapp)
assert the_vapp
print the_vapp.me.name
the_network = vca.get_network(vdc, network)
assert the_network
# this assumes that the vApp is already connected to the network so it
# should return immediately with success
task = the_vapp.connect_to_network(network, the_network.get_href(), 'bridged')
print task.get_status()
assert 'success' == task.get_status()
