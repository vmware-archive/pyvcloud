vcd-cli
=======

[![License](https://img.shields.io/pypi/l/vcd-cli.svg)](https://pypi.python.org/pypi/vcd-cli) [![Stable Version](https://img.shields.io/pypi/v/vcd-cli.svg)](https://pypi.python.org/pypi/vcd-cli) [![Build Status](https://img.shields.io/travis/vmware/vcd-cli.svg?style=flat)](https://travis-ci.org/vmware/vcd-cli/)

Command Line Interface for VMware vCloud Director.

This project is under development, the commands and parameters might change over time. This README usually reflects the syntax of the latest version. More information about commands and usage can be found in the [vcd-cli site](https://vmware.github.io/vcd-cli).

`vcd-cli` uses [pyvcloud](https://github.com/vmware/pyvcloud "Title"), the Python SDK for VMware vCloud Director.

Installation:
=============

In general, `vcd-cli` can be installed with:

``` shell
$ pip install --user vcd-cli
```

The module contains two commands:

- `vca` the current cli
- `vcd` the new cli under development

Validation:

``` shell
$ vca --version

vca-cli 19.0.1 (pyvcloud: 18.0.4.dev35)
```

```shell
$ vcd version

vcd-cli, VMware vCloud Director Command Line Interface, 19.0.1
```

See [vcd-cli wiki](https://github.com/vmware/vcd-cli/wiki) for additional installation details.


Usage:
======

The `--help` option provides a list of available commands and options.

Login:

When the *password* argument is omitted, `vca-cli` prompts the user for the password. By default `vca-cli` caches the password (encrypted) and automatically re-login when the token expires. Below are some examples:

```shell
# vCA
$ vca login 'email@company.com' --password 'p@$$w0rd' \
            --instance 5a872845-6a7e-4e1d-b92a-99c45844417d \
            --vdc vdc1

# vCHS
$ vca login 'email@company.com' --password 'p@$$w0rd' \
            --host vchs.vmware.com

# vCloud Director
$ vca login 'email@company.com' --password 'p@$$w0rd' \
            --host vcdhost.domain.com --org my-org

# vCloud Director with self-signed SSL certificate
$ vca -i login 'email@company.com' --password 'p@$$w0rd' \
      --host vcdhost.domain.com --org my-org
```

Access to a virtual datacenter:

```
$ vca vdc info
Details of Virtual Data Center 'vdc1', profile 'od':
| Type              | Name                   |
|-------------------+------------------------|
| gateway           | gateway                |
| network           | default-routed-network |
| network           | net-101                |
| vdcStorageProfile | SSD-Accelerated        |
| vdcStorageProfile | Standard               |
Compute capacity:
| Resource    |   Allocated |   Limit |   Reserved |   Used |   Overhead |
|-------------+-------------+---------+------------+--------+------------|
| CPU (MHz)   |           0 |  130000 |          0 |      0 |          0 |
| Memory (MB) |           0 |  102400 |          0 |      0 |          0 |
Gateways:
| Name    | External IPs                  | DHCP   | Firewall   | NAT   | VPN   | Networks                        | Syslog   | Uplinks      | Selected   |
|---------+-------------------------------+--------+------------+-------+-------+---------------------------------+----------+--------------+------------|
| gateway | 107.189.88.182, 107.189.90.65 | On     | Off        | On    | Off   | net-101, default-routed-network |          | d4p14v14-ext | *          |
```

Logout:

```
$ vca logout
Logout successful for profile 'default'
```

Login with Session ID and SAML Support
---

We are currently developing integration with SAML for single-sign on. For vCloud Director
instances configured with SAML, login can be accomplished by specifying a valid session id or
using a browser in the same computer.

Login with a browser:

1. Using Google `chrome`, login to vCloud Director
2. On a command line, run the command:

```
$ vcd login vcd-host.vmware.com my-organization my_user_id --use-browser-session
my_user_id logged in, org: 'my-organization', vdc: 'my-vdc'
```

Login with a valid session id:

```
$ vcd login session list chrome
host                       session_id
--------------------------- --------------------------------
vcd-host.vmware.com         ee968665bf3412d581bbc6192508eec4
test-host1.eng.vmware.com   9f8d61446e464648aad40c59964d3fe0
test-host2.eng.vmware.com   2b90cb9adf924ef7b5346ae9b4177bad

$ vcd login vcd-host.vmware.com my-organization my_user_id \
      --session-id ee968665bf3412d581bbc6192508eec4
my_user_id logged in, org: 'my-organization', vdc: 'my-vdc'
```

This feature can be combined with the new functionality for uploading and downloading
templates and iso files with `vcd-cli` for convenient file transfers in SAML enabled
vCloud Director instances.

vCloud Air Support
---

We are transitioning to a new `vcd-cli` tool that eventually will replace `vca-cli`. The new `vcd-cli` will continue to support vCloud Air.

To login to vCloud Air with the new `vcd-cli`:

- Locate the `vCloud Director API URL` link in the vCloud Air console, for example: `https://p1v17-vcd.vchs.vmware.com:443/cloud/org/20-162/`
- Identify the organization name at the end of the URL, `20-162` in the example.
- Use your email and password in the `login` command.

The general syntax of the `login` command is:

```shell
$ vcd login [OPTIONS] host organization user
```

Sample login to a vCA subscription service:

```shell
$ vcd login p1v17-vcd.vchs.vmware.com 20-162 'user@company.com' \
            --password 'p@$$w0rd'
```

Sample login to a vCA on-demand service:

```shell
$ vcd login us-texas-1-14.vchs.vmware.com/api/compute ad96259e-2d36-44ad-9dd7-4586d45b43ca \
            'user@company.com' --password 'p@$$w0rd'
```

Development
---

macOS:

```shell
$ git clone https://github.com/vmware/vcd-cli.git
$ cd vcd-cli
$ pip install oslo.utils cryptography
$ python setup.py develop
```
