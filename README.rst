pyvcloud
========

|docs-latest| |pip| |ver| |build-status|

Python SDK for VMware vCloud. It supports vCloud Air On Demand and Subscription. It also supports vCloud Director.

``Release early, release often.``

This project is under development, the classes, methods and parameters might change over time. This README usually reflects the syntax of the latest version.

Sample usage:

Import modules and instantiate a vCloud Air object::

    from pyvcloud.vcloudair import VCA
    vca = VCA(host, user, service_type, service_version, verify)

Login to a vCloud Director instance::

    result = vca.login(password=password, org=org)
 
   
See `changes log <http://pyvcloud.readthedocs.org/en/latest/changes.html>`_ for a list of changes.

Installation
============

The Python SDK requires the libxml2 and libxslt libraries, see `lxml <http://lxml.de/installation.html>`_ for more details. 

On Debian/Ubuntu, you can install `lxml` and Python development dependencies with this command:

    sudo apt-get install libxml2-dev libxslt-dev python-dev python-pip

On RHEL-based distributions:

    sudo yum install libxslt-devel libxml2-devel python-devel python-pip

The Python SDK can then be installed with the following command:

    pip install pyvcloud
    
Use of `virtualenv <http://docs.python-guide.org/en/latest/dev/virtualenvs/>`_ is recommended.


Usage
=====

The SDK supports logging in to different type of services: vCloud Air Subscription, vCloud Air On Demand and vCloud Director Standalone. See the following `code <https://github.com/vmware/pyvcloud/blob/master/examples/examples.py>`_ as an example::

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

    ### Subscription
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


    ### On Demand            
    host='iam.vchs.vmware.com'
    username = os.environ['VCAUSER']
    password = os.environ['PASSWORD']
    instance = 'c40ba6b4-c158-49fb-b164-5c66f90344fa'
    org = 'a6545fcb-d68a-489f-afff-2ea055104cc1'
    vdc = 'VDC1'
    vapp = 'ubu'

    #sample login sequence on vCloud Air On Demand
    vca = VCA(host=host, username=username, service_type='ondemand', version='5.7', verify=True)

    #first login, with password
    result = vca.login(password=password)
    print_vca(vca)

    #then login with password and instance id, this will generate a session_token
    result = vca.login_to_instance(password=password, instance=instance, token=None, org_url=None)
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


    ### vCloud Director standalone
    host='p1v21-vcd.vchs.vmware.com'
    username = os.environ['VCAUSER']
    password = os.environ['PASSWORD']
    service = '85-719'
    org = 'AppServices'
    vdc = 'AppServices'
    vapp = 'cts'

    #sample login sequence on vCloud Director standalone
    vca = VCA(host=host, username=username, service_type='standalone', version='5.6', verify=True)

    #first login, with password and org name
    result = vca.login(password=password, org=org)
    print_vca(vca)

    #next login, with token, org and org_url, no password, it will retrieve the organization
    result = vca.login(token=vca.token, org=org, org_url=vca.vcloud_session.org_url)
    print_vca(vca)

    #this tests the vcloud session token
    test_vcloud_session(vca, vdc, vapp)

    
Development
===========

To test the current code, check it out from github and install it with::

    pip install --edit .

To debug a python session, add this code::

    import logging
    import httplib
    httplib.HTTPConnection.debuglevel = 1
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True
    

Testing
=======

To test pyvcloud::

    git clone https://github.com/vmware/pyvcloud.git
    cd pyvcloud
    virtualenv .venv
    source .venv/bin/activate
    pip install --edit .
    pip install -r test-requirements.txt
    cp tests/config_example.yaml tests/config_standalone.yaml
    # customize credentials and other parameters
    nosetests --verbosity=2  --tc-format yaml --tc-file tests/config_standalone.yaml \
                tests/vcloud_tests.py

.. |build-status| image:: https://img.shields.io/travis/vmware/pyvcloud.svg?style=flat
    :alt: build status
    :scale: 100%
    :target: https://travis-ci.org/vmware/pyvcloud/

.. |docs| image:: https://readthedocs.org/projects/pyvcloud/badge/?version=stable
    :alt: Documentation Status
    :scale: 100%
    :target: http://pyvcloud.readthedocs.org/en/stable/

.. |docs-latest| image:: https://readthedocs.org/projects/pyvcloud/badge/?version=latest
    :alt: Documentation Status
    :scale: 100%
    :target: http://pyvcloud.readthedocs.org/en/latest/

.. |pip| image:: https://img.shields.io/pypi/dm/pyvcloud.svg
    :alt: Download Status
    :scale: 100%
    :target: https://pypi.python.org/pypi/pyvcloud

.. |ver| image:: https://img.shields.io/pypi/v/pyvcloud.svg
    :alt: Stable Version
    :scale: 100%
    :target: https://pypi.python.org/pypi/pyvcloud

