import os
from pyvcloud import vcloudair
from pyvcloud.vcloudair import VCA


username = os.environ['VCAUSER']
password = os.environ['VCAPASS']
service_type = VCA.VCA_SERVICE_TYPE_VCHS
host = 'vchs.vmware.com'
version = '5.6'
vca = VCA(host=host, username=username, service_type=service_type,
          version=version, verify=True, log=True)
assert vca
result = vca.login(password=password)
assert result
assert vca.token
service = 'M684216431-4470'
org = 'M684216431-4470'
result = vca.login_to_org(service, org)
assert result
vdc = 'M684216431-4470'
the_vdc = vca.get_vdc(vdc)
assert the_vdc
print 'vdc name: ' + the_vdc.get_name()
print 'catalogs: '
for catalog in vca.get_catalogs():
    print '  - ' + catalog.get_name()

