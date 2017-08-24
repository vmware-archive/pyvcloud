#! /usr/bin/env python

import json
import time, datetime, os, sys
from pyvcloud.vcloudair import VCA
from pyvcloud.task import Task
from pyvcloud.helper.CommonUtils import convertPythonObjToStr

host         = sys.argv[1]
org_id       = sys.argv[2]
vcloud_token = sys.argv[3]

org_url = 'https://%s/api/org/%s' % (host, org_id)
verify = False
log = True
version = '27.0'

vca_tenant = VCA(host=host, username='', service_type='vcd', version=version, verify=verify, log=log)
assert(vca_tenant)
result = vca_tenant.login(token=vcloud_token, org='', org_url=org_url)
assert(result == True)
o = vca_tenant.vcloud_session.organization
print('this is org: %s' % o.get_name())
