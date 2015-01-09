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
    vcd = vca.get_vCloudDirector()

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

Create a vApp and connect it to an organization network::

    vapp = vcd.create_vApp('myvapp', 'ubuntu_1204_64bit', 'blueprints', {'--blocking': False, '--json': True, '--deploy': False, '--on': False, '--network': 'AppServices-default-routed', '--fencemode': 'bridged'})    



