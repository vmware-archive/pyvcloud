pyvcloud
========

|ver| |build-status|

Python SDK for VMware vCloud Director and vCloud Air.

This project is under development, the classes, methods and parameters might change over time. This README usually reflects the syntax of the latest version.

New vCD support is located under `pyvcloud/vcd <pyvcloud/vcd>`_ directory.

Installation
============

In general, the Python SDK can then be installed with the following command:

.. code:: bash

    pip install --user pyvcloud

**pyvcloud** can also be installed with `virtualenv <http://docs.python-guide.org/en/latest/dev/virtualenvs/>`_

Examples
========

See the `examples <https://github.com/vmware/pyvcloud/blob/master/examples>`_ directory for sample code.

Development and Test
====================

To run the source code, check it out from GitHub and install it with:

.. code:: bash

    python setup.py develop

To test **pyvcloud**:

.. code:: bash

    git clone https://github.com/vmware/pyvcloud.git
    cd pyvcloud
    virtualenv .venv
    source .venv/bin/activate
    python setup.py develop
    pip install -r test-requirements.txt
    cp tests/config.yaml my_config.yaml
    # customize credentials and other parameters
    nosetests --verbosity=2  --tc-format yaml --tc-file my_config.yaml tests/00010_vcd_login.py

See `.gitlab-ci.yml <.gitlab-ci.yml>`_ for current tests.

.. |build-status| image:: https://img.shields.io/travis/vmware/pyvcloud.svg?style=flat
    :alt: build status
    :scale: 100%
    :target: https://travis-ci.org/vmware/pyvcloud/

.. |ver| image:: https://img.shields.io/pypi/v/pyvcloud.svg
    :alt: Stable Version
    :scale: 100%
    :target: https://pypi.python.org/pypi/pyvcloud
