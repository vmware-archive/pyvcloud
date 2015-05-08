import time, datetime, os
from pyvcloud.vcloudair import VCA
from pyvcloud.vapp import VAPP
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


host = 'https://vcd02-2848639.mv.rackspace.com'
username = "dev_pete"
password = "p@ssw0rd"
# instance = '28149a83-0d23-4f03-85e1-eb8be013e4ff'
org = 'dvc02-2848639'
# vdc = 'bf54d657-0158-4a6b-8c4f-19e96451bebc'
vdc_name = 'dvc02-2848639'
template_name = 'RHEL_6.5_Unmanaged'
catalog = 'Rackspace Catalog'
vapp = ''
api = "https://vcd02-2848639.mv.rackspace.com/api/sessions"
#sample login sequence on vCloud Air On Demand
vca = VCA(host=host, username=username, service_type='vcd', version='5.5', verify=False)

#first login, with password
result = vca.login(password=password, org=org)

# print_vca(vca)

vca_2 = VCA(host=host, username=username, service_type='vcd', version='5.5', verify=False)
vca_2.login(password=password, token=vca.vcloud_session.token, org=vca.vcloud_session.org, org_url=vca.vcloud_session.org_url)

net_href = vca_2.get_network(vdc_name, network_name="ExNet-TenDot-vlan1653").get_href()
net_href_2 = vca_2.get_network(vdc_name, network_name="ExNet-Inside-VLAN1470").get_href()


vdc = vca_2.get_vdc(vdc_name)
vapp = vca_2.get_vapp(vdc, 'sample-2')

# vapp.disconnect_vms("ExNet-Inside-VLAN1470")
vapp.disconnect_from_network("ExNet-Inside-VLAN1470")

# vApp_task = vca_2.create_vapp(vdc_name=vdc_name, vapp_name="sample-2", template_name=template_name, catalog_name=catalog)
#
# print "Creating VApp"
# vca_2.block_until_completed(vApp_task)

#time.sleep(60)
#
# vdc = vca_2.get_vdc(vdc_name)
# vapp = vca_2.get_vapp(vdc, 'sample-2')
#
# task_1 = vapp.connect_to_network(network_name="ExNet-TenDot-vlan1653",network_href=net_href)
#
# print "Connecting VAPP to Network 1"
# vca_2.block_until_completed(task_1)
#
# task_2 = vapp.connect_vms(network_name="ExNet-TenDot-vlan1653", connections_primary_index=0,connection_index=0, ip_allocation_mode='POOL')
# print "Connecting VM to Network 1"
# vca_2.block_until_completed(task_2)
#
# vapp = vca_2.get_vapp(vdc, 'sample-2')
#
# # time.sleep(30)
#
# task_3 = vapp.connect_to_network(network_name="ExNet-Inside-VLAN1470",network_href=net_href_2)
# print "Connecting VAPP to Network 2"
# vca_2.block_until_completed(task_3)
# print "Connecting VAPP to Network 2"
# task_4 = vapp.connect_vms(network_name="ExNet-Inside-VLAN1470", connections_primary_index=0,connection_index=1, ip_allocation_mode='POOL')
#
# vca_2.block_until_completed(task_4)
#
# print "Power on"
# vapp.poweron()
# v = VAPP(vapp, vca_2.vcloud_session.get_vcloud_headers(), False)
# vapp.connect_vms(network_name="ExNet-TenDot-vlan269", connections_primary_index=0,connection_index=0)
#time.sleep(60)
# # task_2 = vapp.connect_to_network(network_name="ExNet-Inside-VLAN1468",network_href=net_href_2)
# #
# time.sleep(60)
#

#

#
#time.sleep(80)



#vapp.get_vms_network_info()

#time.sleep(60)

#time.sleep(30)
#vapp.poweron()


# print vApp

# headers = {}
# headers["x-vcloud-authorization"] = vca.vcloud_session.token
# headers["Accept"] = "application/*+xml;version=" + '5.5'
#
# vdc = vca_2.get_vdc(vdc_name)
# vapp = vca_2.get_vapp(vdc, 'TEST-4')
#
# print vapp.connect_vms(network_name='ExNet-Inside-VLAN1468', connection_index=0, connections_primary_index=0)

# v = VAPP(vapp, headers, verify=False)
#
# dep = v.deploy()
#
# print dep
# print vca_2.organization

# vcs = VCS(url=host, username=username, org=org, api_url=api, version='5.5', verify=False)
# vcs.login(password,token=vca.vcloud_session.token)
# print vcs.organization




# def print_vca(vca):
#     if vca:
#         print 'vca token:            ', vca.token
#         if vca.vcloud_session:
#             print 'vcloud session token: ', vca.vcloud_session.token
#             print 'org name:             ', vca.vcloud_session.org
#             print 'org url:              ', vca.vcloud_session.org_url
#             print 'organization:         ', vca.vcloud_session.organization
#         else:
#             print 'vca vcloud session:   ', vca.vcloud_session
#     else:
#         print 'vca: ', vca
#
# def test_vcloud_session(vca, vdc, vapp):
#     the_vdc = vca.get_vdc(vdc)
#     for x in range(1, 5):
#         print datetime.datetime.now(), the_vdc.get_name(), vca.vcloud_session.token
#         the_vdc = vca.get_vdc(vdc)
#         if the_vdc: print the_vdc.get_name(), vca.vcloud_session.token
#         else: print False
#         the_vapp = vca.get_vapp(the_vdc, vapp)
#         if the_vapp: print the_vapp.me.name
#         else: print False
#         time.sleep(2)
#
# ### Subscription
# host='vchs.vmware.com'
# username = os.environ['VCAUSER']
# password = os.environ['PASSWORD']
# service = '85-719'
# org = 'AppServices'
# vdc = 'AppServices'
# vapp = 'cts'
#
# #sample login sequence on vCloud Air Subscription
# vca = VCA(host=host, username=username, service_type='subscription', version='5.6', verify=True)
#
# #first login, with password
# result = vca.login(password=password)
# print_vca(vca)
#
# #next login, with token, no password
# #this tests the vca token
# result = vca.login(token=vca.token)
# print_vca(vca)
#
# #uses vca.token to generate vca.vcloud_session.token
# vca.login_to_org(service, org)
# print_vca(vca)
#
# #this tests the vcloud session token
# test_vcloud_session(vca, vdc, vapp)
#
#
# ### On Demand
# host='iam.vchs.vmware.com'
# username = os.environ['VCAUSER']
# password = os.environ['PASSWORD']
# instance = '28149a83-0d23-4f03-85e1-eb8be013e4ff'
# org = '8e479bba-862d-417e-a69f-c35aa50b8d95'
# vdc = 'VDC1'
# vapp = 'ubu'
#
# #sample login sequence on vCloud Air On Demand
# vca = VCA(host=host, username=username, service_type='ondemand', version='5.7', verify=True)
#
# #first login, with password
# result = vca.login(password=password)
# print_vca(vca)
#
# #then login with password and instance id, this will generate a session_token
# result = vca.login_to_instance(password=password, instance=instance, token=None, org_url=None)
# print_vca(vca)
#
# #next login, with token, org and org_url, no password, it will retrieve the organization
# result = vca.login_to_instance(instance=instance, password=None, token=vca.vcloud_session.token, org_url=vca.vcloud_session.org_url)
# print_vca(vca)
#
# #this tests the vca token
# result = vca.login(token=vca.token)
# if result: print result, vca.instances
# else: print False
#
# #this tests the vcloud session token
# test_vcloud_session(vca, vdc, vapp)
#
#
# ### vCloud Director standalone
# host='p1v21-vcd.vchs.vmware.com'
# username = os.environ['VCAUSER']
# password = os.environ['PASSWORD']
# service = '85-719'
# org = 'AppServices'
# vdc = 'AppServices'
# vapp = 'cts'
#
# #sample login sequence on vCloud Air Subscription
# vca = VCA(host=host, username=username, service_type='vcd', version='5.6', verify=True)
#
# #first login, with password and org name
# result = vca.login(password=password, org=org)
# print_vca(vca)
#
# #next login, with token, org and org_url, no password, it will retrieve the organization
# result = vca.login(token=vca.token, org=org, org_url=vca.vcloud_session.org_url)
# print_vca(vca)
#
# #this tests the vcloud session token
# test_vcloud_session(vca, vdc, vapp)

