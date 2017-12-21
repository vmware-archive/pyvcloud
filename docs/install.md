`vcd-cli` requires Python 3.

## Ubuntu


Ubuntu 16.04:

``` shell
    $ sudo apt-get install python3-pip gcc python3-dev -y

    $ pip3 install --user vcd-cli
```

## CentOS


CentOS 7:

```shell
    $ sudo yum install epel-release python34 python34-devel python34-setuptools -y

    $ sudo easy_install-3.4 pip

    $ pip3 install --user vcd-cli
```

## macOS

On macOS, open a Terminal and enter the commands listed below (skip those that refer to a component already installed on your mac):

Install `Xcode Command Line Tools`:

``` shell
    $ xcode-select --install
```

Press `Install` and accept the license terms.

Install `pip`:

``` shell
    $ sudo easy_install pip
```

Install `vcd-cli`

``` shell
    $ pip install --user vcd-cli
```

## Verify Installation

Display the version installed:

``` shell
    $ vcd version

    vcd-cli, VMware vCloud Director Command Line Interface, 19.2.3
```

## Installation with virtualenv

It is also possible to install `vcd-cli` in a [virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/).

## Upgrade

To upgrade an existing `vcd-cli` install, just run:

``` shell
    $ pip install --user vcd-cli --upgrade
```

## Pre-releases

The commands described above install the current stable version of `vcd-cli`. To install a pre-release version, enter:

``` shell
    $ pip install --user vcd-cli --pre
```

And to upgrade a pre-release:

``` shell
    $ pip install vcd-cli --pre --upgrade
```

Installation from the current development version in GitHub:

``` shell
    $ pip install --user git+https://github.com/vmware/vcd-cli.git
```
