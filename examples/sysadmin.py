#! /usr/bin/env python

import json
import time, datetime, os, sys
from pyvcloud.vcloudair import VCA
from pyvcloud.system import System
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

system = System(session=vca.vcloud_session, verify=verify, log=log)
# orgs = system.get_orgs()
# print(json.dumps(orgs))

extensions = system.get_extensions()
print(extensions)

sys.exit(0)

extension_name = 'gcp-ticketing'
extension_metadata = """
<vmext:Service xmlns="http://www.vmware.com/vcloud/v1.5" xmlns:vmext="http://www.vmware.com/vcloud/extension/v1.5" name="%s">
   <vmext:Namespace>%s</vmext:Namespace>
   <vmext:Enabled>true</vmext:Enabled>
   <vmext:RoutingKey>%s</vmext:RoutingKey>
   <vmext:Exchange>vcdext</vmext:Exchange>
   <vmext:ApiFilters>
      <vmext:ApiFilter>
         <vmext:UrlPattern>(/api/org/.*/%s/*[0-9]*)</vmext:UrlPattern>
      </vmext:ApiFilter>
   </vmext:ApiFilters>
</vmext:Service>
""" % (extension_name, extension_name, extension_name, extension_name)

result = system.register_extension(extension_metadata)
print(result)

extension = system.get_extension(extension_name)
if extension == None:
    print('extension %s not found' % extension_name)
else:
    print(json.dumps(extension))
