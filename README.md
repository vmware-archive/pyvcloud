vca-cli
=======

[![Stable Version](https://img.shields.io/pypi/v/vca-cli.svg)](https://pypi.python.org/pypi/vca-cli) [![Build Status](https://img.shields.io/travis/vmware/vca-cli.svg?style=flat)](https://travis-ci.org/vmware/vca-cli/)

Command Line Interface for VMware vCloud Director. It also supports vCloud Air.

This project is under development, the commands and parameters might change over time. This README usually reflects the syntax of the latest version. More information about commands and usage can be found in the [vca-cli wiki](https://github.com/vmware/vca-cli/wiki). See the [release notes](https://github.com/vmware/vca-cli/wiki/ReleaseNotes) for what's new.

`vca-cli` uses [pyvcloud](https://github.com/vmware/pyvcloud "Title"), a Python SDK for VMware vCloud Director.

Installation:
=============

In general, `vca-cli` can be installed with:

``` shell
    $ pip install --user vca-cli
```

Check installation with:

``` shell
    $ vcd --version

    vca-cli version 18 (pyvcloud: 18.0.2)
```

See [vca-cli wiki](https://github.com/vmware/vca-cli/wiki) for additional installation details.


Usage:
======

Login and Logout:
-----------------

When the *password* argument is omitted, `vca-cli` will prompt the user for the password. By default `vca-cli` caches the password (encrypted) and automatically re-login when the token expires. Below are some examples:

    # vCA, password prompt
    vca login email@company.com
    Password: ***************

    # vCA
    $ vca login email@company.com --password ********

    # vCHS
    $ vca login email@company.com --password ******** \
                --host vchs.vmware.com --version 5.6

    # vCloud Director Standalone
    $ vca login email@company.com --password ******** \
                --host vcdhost.domain.com --org myorg --version 5.6

    # vCloud Director with insecure SSL certificate
    $ vca --insecure login email@company.com --password ******** \
          --host vcdhost.domain.com --org myorg --version 5.6

vCloud Air (vCA) example of login and access to a VDC:

    $ vca login email@company.com --password ********
    User 'email@company.com' logged in, profile 'default'
    Password encrypted and saved in local profile. Use --do-not-save-password to disable it.

    $ vca instance
    Available instances for user 'email@company.com', profile 'default':
    | Service Group   | Region            | Plan                           | Instance Id                                                  | Selected   |
    |-----------------+-------------------+--------------------------------+--------------------------------------------------------------+------------|
    | M748916508      | au-south-1-15     | Virtual Private Cloud OnDemand | 5f444142-9479-48a7-a70a-c8964a35c5ce                         |            |
    | M748916508      | us-virginia-1-4   | Virtual Private Cloud OnDemand | d7a623de-1183-46a9-9b02-9043ca68f441                         |            |
    | M748916508      | us-california-1-3 | Virtual Private Cloud OnDemand | b50d1558-db46-4afb-97d1-2c4d23e4b8a9                         |            |
    | M748916508      | uk-slough-1-6     | Virtual Private Cloud OnDemand | ab45a63a-f01c-41e8-9e02-acbb4be05a0d                         |            |
    | M748916508      | de-germany-1-16   | Virtual Private Cloud OnDemand | 95e04439-7dcc-42e3-90ec-36ef2e4b0757                         |            |
    | M748916508      | us-texas-1-14     | Virtual Private Cloud OnDemand | 5a872845-6a7e-4e1d-b92a-99c45844417d                         |            |
    | M748916508      | us-california-1-3 | Object Storage powered by EMC  | d1099f7b-34ee-4723-a113-802622aaf3f1:os.vca.vmware.4562.6481 |            |

    $ vca instance use --instance 5a872845-6a7e-4e1d-b92a-99c45844417d
    Using instance:org '5a872845-6a7e-4e1d-b92a-99c45844417d':'e01d04b3-2d86-442e-84a7-4ff194ae9a3d', profile 'default'
    Using VDC 'vdc1', profile 'default'

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

Login and access the VDC in one command:

    $ vca login email@company.com --password ******** \
                --instance 5a872845-6a7e-4e1d-b92a-99c45844417d \
                --vdc vdc1
    User 'email@company.com' logged in, profile 'default'
    Password encrypted and saved in local profile. Use --do-not-save-password to disable it.
    Using instance:org '5a872845-6a7e-4e1d-b92a-99c45844417d':'e01d04b3-2d86-442e-84a7-4ff194ae9a3d', profile 'default'
    Using VDC 'vdc1', profile 'default'

Connection status:

    $ vca status
    Status:
    | Key              | Value                                                          |
    |------------------+----------------------------------------------------------------|
    | vca_cli_version  | 14                                                             |
    | pyvcloud_version | 14                                                             |
    | profile_file     | /Users/francisco/.vcarc                                        |
    | profile          | default                                                        |
    | host             | https://vca.vmware.com                                         |
    | host_score       | https://score.vca.io                                           |
    | user             | email@company.com                                              |
    | instance         | 5a872845-6a7e-4e1d-b92a-99c45844417d                           |
    | org              | e01d04b3-2d86-442e-84a7-4ff194ae9a3d                           |
    | vdc              | vdc1                                                           |
    | gateway          | gateway                                                        |
    | password         | <encrypted>                                                    |
    | type             | vca                                                            |
    | version          | 5.7                                                            |
    | org_url          | https://us-texas-1-14.vchs.vmware.com/api/compute/api/sessions |
    | active session   | True                                                           |

Logout:

    $ vca logout
    Logout successful for profile 'default'

Examples and Help:
------------------

`vca-cli` provides a list of examples with the `example` command:

``` shell
    $ vcd example
```

Syntax, commands and arguments:

``` shell
    $ vcd --help
    Usage: vca [OPTIONS] COMMAND [ARGS]...

      VMware vCloud Air Command Line Interface.

    Options:
      -p, --profile <profile>    Profile id
      -f, --profile-file <file>  Profile file
      -v, --version              Show version
      -d, --debug                Enable debug
      -j, --json                 Results as JSON object
      -i, --insecure             Perform insecure SSL connections
      -h, --help                 Show this message and exit.

    Commands:
      blueprint   Operations with Blueprints
      catalog     Operations with Catalogs
      deployment  Operations with Deployments
      dhcp        Operations with Edge Gateway DHCP Service
      disk        Operations with Independent Disks
      event       Operations with Blueprint Events
      example     vCloud Air CLI Examples
      firewall    Operations with Edge Gateway Firewall Service
      gateway     Operations with Edge Gateway
      instance    Operations with Instances
      login       Login to a vCloud service
      logout      Logout from a vCloud service
      nat         Operations with Edge Gateway NAT Rules
      network     Operations with Networks
      org         Operations with Organizations
      profile     Show profiles
      role        Operations with Roles
      status      Show current status
      user        Operations with Users
      vapp        Operations with vApps
      vdc         Operations with Virtual Data Centers
      vm          Operations with VMs
      vpn         Operations with Edge Gateway VPN
```

Detailed syntax for a specific command:

``` shell
    $ vcd vapp --help
    Usage: vca vapp [OPTIONS] [list | info | create | delete | power-on | power-
                    off | deploy | undeploy | customize | insert | eject | connect
                    | disconnect | attach | detach]

      Operations with vApps

    Options:
      -v, --vdc <vdc>                 Virtual Data Center Name
      -a, --vapp <vapp>               vApp name
      -c, --catalog <catalog>         Catalog name
      -t, --template <template>       Template name
      -n, --network <network>         Network name
      -m, --mode [pool, dhcp, manual]
                                      Network connection mode
      -V, --vm <vm>                   VM name
      -f, --file <customization_file>
                                      Guest OS Customization script file
      -e, --media <media>             Virtual media name (ISO)
      -d, --disk <disk_name>          Disk Name
      -o, --count <count>             Number of vApps to create
      -p, --cpu <virtual CPUs>        Virtual CPUs
      -r, --ram <MB RAM>              Memory in MB
      -i, --ip <ip>                   IP address
      -h, --help                      Show this message and exit.
```
