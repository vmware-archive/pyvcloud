import time, datetime, os
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
    for x in range(1, 5):
        print datetime.datetime.now(), the_vdc.get_name(), vca.vcloud_session.token
        the_vdc = vca.get_vdc(vdc)       
        if the_vdc: print the_vdc.get_name(), vca.vcloud_session.token
        else: print False                
        the_vapp = vca.get_vapp(the_vdc, vapp)
        if the_vapp: print the_vapp.me.name
        else: print False
        time.sleep(2)


##############################
### Subscription
##############################

host='vchs.vmware.com'
username = os.environ['VCAUSER']
password = os.environ['PASSWORD']
service = '85-719'
org = 'AppServices'

vdc = 'AppServices'
vapp = 'cts'

#sample login sequence on vCloud Air Subscription
vca = VCA(host=host, username=username, service_type='subscription', version='5.6', verify=True)

#first login, with password
result = vca.login(password=password)
print_vca(vca)

#next login, with token, no password
#this tests the vca token
result = vca.login(token=vca.token)
print_vca(vca)

#uses vca.token to generate vca.vcloud_session.token
vca.login_to_org(service, org)
print_vca(vca)

#this tests the vcloud session token
test_vcloud_session(vca, vdc, vapp)


##############################
### On Demand            
##############################

host='iam.vchs.vmware.com'
username = os.environ['VCAUSER']
password = os.environ['PASSWORD']
instance = '28149a83-0d23-4f03-85e1-eb8be013e4ff'

vdc = 'VDC1'
vapp = 'ubu'

#sample login sequence on vCloud Air On Demand
vca = VCA(host=host, username=username, service_type='ondemand', version='5.7', verify=True)

#first login, with password
result = vca.login(password=password)
print_vca(vca)

#then login with password and instance id, this will generate a session_token
result = vca.login_to_instance(password=password, instance=instance)
print_vca(vca)

#next login, with token, org and org_url, no password, it will retrieve the organization
result = vca.login_to_instance(instance=instance, password=None, token=vca.vcloud_session.token, org_url=vca.vcloud_session.org_url)
print_vca(vca)

#this tests the vca token        
result = vca.login(token=vca.token)
if result: print result, vca.instances
else: print False

#this tests the vcloud session token
test_vcloud_session(vca, vdc, vapp)


##############################
### vCloud Director standalone
##############################

host='p1v21-vcd.vchs.vmware.com'
username = os.environ['VCAUSER']
password = os.environ['PASSWORD']
org = 'AppServices'

vdc = 'AppServices'
vapp = 'cts'

#sample login sequence on vCloud Air Subscription
vca = VCA(host=host, username=username, service_type='vcd', version='5.6', verify=True)

#first login, with password and org name
result = vca.login(password=password, org=org)
print_vca(vca)

#next login, with token, org and org_url, no password, it will retrieve the organization
result = vca.login(token=vca.token, org=org, org_url=vca.vcloud_session.org_url)
print_vca(vca)

#this tests the vcloud session token
test_vcloud_session(vca, vdc, vapp)

