# vcd-cli

[![License](https://img.shields.io/pypi/l/vcd-cli.svg)](https://pypi.python.org/pypi/vcd-cli) [![Stable Version](https://img.shields.io/pypi/v/vcd-cli.svg)](https://pypi.python.org/pypi/vcd-cli) [![Build Status](https://img.shields.io/travis/vmware/vcd-cli.svg?style=flat)](https://travis-ci.org/vmware/vcd-cli/)

`vcd-cli` is the Command Line Interface for VMware vCloud Director.

## Quick Start

Below is a sample `vcd-cli` interaction with vCloud Director to create a virtual machine and start using it.

Detailed command syntax and usage can be found in the [vcd-cli site](https://vmware.github.io/vcd-cli), along with the [installation](https://vmware.github.io/vcd-cli/install) instructions.

```shell

    $ vcd login myserviceprovider.com org1 usr1 --password secure_pass -w -i
    usr1 logged in, org: 'org1', vdc: 'vdc1'

    $ vcd catalog create catalog1
    task: 893bff31-4bf6-48a6-84b8-55cee97e8349, Created Catalog catalog1(cc0a2b88-9e5a-4391-936f-df6e7902504b), result: success

    $ vcd catalog upload catalog1 photon-custom-hw11-2.0-304b817.ova
    upload 113,169,920 of 113,169,920 bytes, 100%
    property    value
    ----------  ----------------------------------
    file        photon-custom-hw11-2.0-304b817.ova
    size        113207424

    $ vcd vapp create vapp1 --catalog catalog1 --template photon-custom-hw11-2.0-304b817.ova \
      --network net1 --accept-all-eulas
    task: 0f98685a-d11c-41d0-8de4-d3d4efad183a, Created Virtual Application vapp1(8fd8e774-d8b3-42ab-800c-a4992cca1fc2), result: success

    $ vcd vapp list
    isDeployed    isEnabled      memoryAllocationMB  name      numberOfCpus    numberOfVMs  ownerName    status        storageKB  vdcName
    ------------  -----------  --------------------  ------  --------------  -------------  -----------  ----------  -----------  ---------
    true          true                         2048  vapp1                1              1  usr1         POWERED_ON     16777216  vdc1

    $ vcd vapp info vapp1
    property                     value
    ---------------------------  -------------------------------------
    name                         vapp1
    owner                        ['usr1']
    status                       Powered on
    vapp-net-1                   net1
    vapp-net-1-mode              bridged
    vm-1: 1 virtual CPU(s)       1
    vm-1: 2048 MB of memory      2,048
    vm-1: Hard disk 1            17,179,869,184 byte
    vm-1: Network adapter 0      DHCP: 10.150.221.213
    vm-1: computer-name          PhotonOS-001
    vm-1: password               I!8z#z2N

    $ ssh root@10.150.221.213
    ...
```

The OVA used in the example can be downloaded with the command:

```shell
   $ wget http://dl.bintray.com/vmware/photon/2.0/GA/ova/photon-custom-hw11-2.0-304b817.ova
```
## Documentation

See the [vcd-cli site](https://vmware.github.io/vcd-cli) for detailed documentation and installation instructions.

Please note that this project is under development, the commands, parameters and options might change over time.

`vcd-cli` uses [pyvcloud](https://github.com/vmware/pyvcloud "Title"), the Python SDK for VMware vCloud Director. It requires Python 3.

Previous versions and deprecated code can be found in this repository under [tag 19.2.3](https://github.com/vmware/vcd-cli/tree/19.2.3).

## Contributing

The `vcd-cli` project team welcomes contributions from the community. Before you start working with `vcd-cli`, please read our [Developer Certificate of Origin](https://cla.vmware.com/dco). All contributions to this repository must be signed as described on that page. Your signature certifies that you wrote the patch or have the right to pass it on as an open-source patch. For more detailed information, refer to [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[Apache-2.0](LICENSE.txt)
