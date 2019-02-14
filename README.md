## pyvcloud

[![License](https://img.shields.io/pypi/l/pyvcloud.svg)](https://pypi.python.org/pypi/pyvcloud) [![Stable Version](https://img.shields.io/pypi/v/pyvcloud.svg)](https://pypi.python.org/pypi/pyvcloud) [![Build Status](https://img.shields.io/travis/vmware/pyvcloud.svg?style=flat)](https://travis-ci.org/vmware/pyvcloud/)

`pyvcloud` is the Python SDK for VMware vCloud Director.

## Installation

In general, `pyvcloud` can be installed with the following command:
```shell
$ pip install --user pyvcloud
```
Depending on your operating system and distribution you
may need additional packages to install successfully. See
[install.md](docs/install.md) for full details.

## Testing

Contributions to `pyvcloud` are welcome and it should include unit tests. See the [contributing guide](CONTRIBUTING.md) for details.

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

See [tests](tests/) for a list of current unit tests written for the new SDK implementation.


## Notes

Please note that this project is under development and the interfaces might change over time.

`pyvcloud` is used by [vcd-cli](https://vmware.github.io/vcd-cli), the Command Line Interface for VMware vCloud Director. It requires Python 3.6 or higher.

Previous versions and deprecated code can be found in this repository under [tag 18.2.2](https://github.com/vmware/pyvcloud/tree/18.2.2).

## Contributing

The `pyvcloud` project team welcomes contributions from the community. Before you start working with `pyvcloud`, please read our [Developer Certificate of Origin](https://cla.vmware.com/dco). All contributions to this repository must be signed as described on that page. Your signature certifies that you wrote the patch or have the right to pass it on as an open-source patch. For more detailed information, refer to [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[Apache-2.0](LICENSE.txt)
