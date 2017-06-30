#! /usr/bin/env python

import json
import time, datetime, os, sys
from pyvcloud.vcloudair import VCA
from pyvcloud.system import System
from pyvcloud.helper.CommonUtils import convertPythonObjToStr
from lxml import etree

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
username = 'usr1'
password = os.environ['PASSWORD']
org = 'org1'
org_url = 'https://%s/cloud/org/org1' % host
verify = False
log = True
version = '27.0'
vdc = 'o1vdc1'
name = sys.argv[1]

vca = VCA(host=host, username=username, service_type='vcd', version=version, verify=verify, log=log)

result = vca.login(password=password, org=org, org_url=org_url)
result = vca.login(token=vca.token, org=org, org_url=vca.vcloud_session.org_url)
print_vca(vca)
the_vdc = vca.get_vdc(vdc)
for entity in the_vdc.get_ResourceEntities().ResourceEntity:
    if entity.type_ == 'application/vnd.vmware.vcloud.vApp+xml':
        if entity.name == name:
            print('name=%s, href=%s' % (entity.name, entity.href))
            metadata = vca.get_vapp_metadata(entity.href)
            x = etree.fromstring(metadata)
            entries = x.xpath('//xmlns:MetadataEntry', namespaces={'xmlns':'http://www.vmware.com/vcloud/v1.5'})
            for entry in entries:
                for c in list(entry):
                    localname = c.tag.split('}')[1]
                    if localname == 'Link':
                        continue
                    elif localname == 'TypedValue':
                        localname = 'Value'
                        value = list(c)[0].text
                    elif localname == 'Domain':
                        localname = 'Domain/%s' % c.attrib['visibility']
                        value = c.text
                    else:
                        value = c.text
                    print('    %s: %s' % (localname, value))
                print('')
            print('')
