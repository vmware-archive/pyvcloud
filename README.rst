pyvcloud
========

Python SDK for VMware vCloud.

``Release early, release often.``

This project is under development.

Sample usage:

Login to a vCloud Director instance::

    from pyvcloud.vcloudair import VCA
    vca = VCA()
    vca.login('vcdhost.company.com', 'vcdUser@vcdOrg', 'password', None, 'vcd', '5.6')
    vcd = vca.get_vCloudDirector()


Get all vApps::

    vapps = vcd.get_vApps()
    for vapp in vapps:
        print "name: %s, status: %s\n" % (vapp.name, vapp.status)

Get all vApp templates::

    templates = vcd.list_templates({'--catalog': False})

Get all networks::

    networks = vcd.get_networkRefs()

Create a vApp and connect it to an organization network::

    vapp = vcd.create_vApp('vapp2', 'ubuntu_1204_64bit', 'blueprints', {'--blocking': False, '--json': True, '--deploy': False, '--on': False, '--network': 'AppServices-default-routed', '--fencemode': 'bridged'})    



