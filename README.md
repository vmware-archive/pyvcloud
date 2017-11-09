pyvcloud
---

[![License](https://img.shields.io/pypi/l/pyvcloud.svg)](https://pypi.python.org/pypi/pyvcloud) [![Stable Version](https://img.shields.io/pypi/v/pyvcloud.svg)](https://pypi.python.org/pypi/pyvcloud) [![Build Status](https://img.shields.io/travis/vmware/pyvcloud.svg?style=flat)](https://travis-ci.org/vmware/pyvcloud/)

`pyvcloud` is the Python SDK for VMware vCloud Director.

This project is under development, the classes, methods and parameters might change over time. This README usually reflects the syntax of the latest version.

We are rewriting `pyvcloud` for a more efficient and easy-to-use library. The new code is located under the [pyvcloud/vcd](pyvcloud/vcd) directory. The original code is still part of the SDK but we encourage to use (and contribute to) the new library. The new [vcd-cli](https://vmware.github.io/vcd-cli) is being developed with the new library implementation and can be used as a reference, in addition to the [unit tests](tests/run-tests.sh).


Installation
---

In general, `pyvcloud` can be installed with the following command:

```shell
$ pip install --user pyvcloud
```

`pyvcloud` can also be installed with [virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs).


Testing
---

Contributions to `pyvcloud` are welcome and they should include unit tests.

Check out the latest version and install:

```shell
git clone https://github.com/vmware/pyvcloud.git
cd pyvcloud
virtualenv .venv
source .venv/bin/activate
python setup.py develop
```

Sample test parameters are in file [tests/config.yml](tests/config.yml). Create a copy to specify your own settings and use the `VCD_TEST_CONFIG_FILE` env variable.

```shell
cd tests
cp config.yml private.config.yml
# customize credentials and other parameters
export VCD_TEST_CONFIG_FILE=private.config.yml
# run unit test
python -m unittest vcd_login vcd_catalog_setup
# run just a test method
python -m unittest vcd_catalog_setup.TestCatalogSetup.test_validate_ova
```

See [tests/run-tests.sh](tests/run-tests.sh) for a list of current unit tests written for the new SDK implementation.
