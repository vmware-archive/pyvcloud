pyvcloud
========

Python SDK for VMware vCloud.

``Release early, release often.``

This project is under development.

Sample usage:

Import modules and instantiate a vCloud Air object::

    from pyvcloud.vcloudair import VCA
    vca = VCA()

Login to a vCloud Director instance::

    vca.login('vcdhost.company.com', 'vcdUser@vcdOrg', 'password', None, 'vcd', '5.6')
    
A user might have access to one or more datacenters within an organization::

    for datacenter in vca.get_vdcReferences():
        print datacenter.name        
    vcd = vca.get_vCloudDirector(vdcId='mydatacenter')

Login to subscription-based vCloud Air::

    vca.login('vchs.vmware.com', 'user@company.com', 'password', None, 'subscription', '5.6')  
    
On the subscription-based vCloud Air, there are services and datacenters::

    for service in vca.get_serviceReferences():
        print service.serviceId  
    
    for datacenter in vca.get_vdcReferences('myservice'):
        print datacenter.name
        
    vcd = vca.get_vCloudDirector('myservice', 'mydatacenter')

In both cases, after getting a reference to a vCloud Director instance (vcd), get all vApps::

    for vapp in vcd.get_vApps():
        print "name: %s, status: %s\n" % (vapp.name, vapp.status)

Get all vApp templates::

    templates = vcd.list_templates({'--catalog': False})

Get all networks::

    networks = vcd.get_networkRefs()

Sample vApp life cycle::

    #create vApp and get the reference
    vcd.create_vApp('myvapp', 'Ubuntu Server 12.04 LTS (amd64 20140927)', 'Public Catalog', {'--blocking': True, '--json': True, '--deploy': False, '--on': False, '--network': ''})
    vapp = vcd.get_vApp('myvapp')

    #connect vApp to org network
    vcd.connect_vApp(vapp, 'AppServices-default-routed', 'bridged')
    
    #In some cases, the vApp template is connected to the default 'VM Network',
    #in those cases it is safe to disconnect the vApp from that network
    vapp.disconnect_from_network('VM Network')

    #connect the VMs
    vapp.connect_vms('AppServices-default-routed', 'POOL')
    
    #power on the vApp and VMs
    vapp.poweron()
    
The vApp is now ready to use. When is time to delet it (need to get the vapp reference before each operation)::

    vapp = vcd.get_vApp('myvapp')
    vapp.undeploy(action='shutdown')

    vapp = vcd.get_vApp('myvapp')
    vapp.delete()    

Displaying the XML representation of the vApp::

    import sys
    myvapp.me.export(sys.stdout, 0)


Development
===========

To test the current code, check it out from github and install it with::

    pip install --editable .

To debug a python session, add this code::

    import logging
    import httplib
    httplib.HTTPConnection.debuglevel = 1
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True

