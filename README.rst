pyvcloud
========

Python SDK for VMware vCloud. It supports vCloud Air On Demand and Subscription. It also supports vCloud Director.

``Release early, release often.``

This project is under development, the classes, methods and parameters might change over time. This README usually reflects the syntax of the latest version.

Sample usage:

Import modules and instantiate a vCloud Air object::

    from pyvcloud.vcloudair import VCA
    vca = VCA(host, user, service_type, service_version, verify)

Login to a vCloud Director instance::

    result = vca.login(password=password, org=org)


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

