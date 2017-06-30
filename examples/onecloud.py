#! /usr/bin/env python

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
### vCloud Director standalone
##############################

host='vcore3-us01.oc.vmware.com'
username = 'usr1'
password = os.environ['PASSWORD']
org = 'sandbox'
org_url = 'https://vcore3-us01.oc.vmware.com/cloud/org/sandbox'


vca = VCA(host=host, username=username, service_type='standalone', version='5.6', verify=True, log=True)

result = vca.login(password=password, org=org, org_url=org_url)
print_vca(vca)
