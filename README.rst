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

