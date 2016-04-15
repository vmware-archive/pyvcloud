vca-cli
=======

[![Download Status](https://img.shields.io/pypi/dm/vca-cli.svg)](https://pypi.python.org/pypi/vca-cli) [![Stable Version](https://img.shields.io/pypi/v/vca-cli.svg)](https://pypi.python.org/pypi/vca-cli) [![Build Status](https://img.shields.io/travis/vmware/vca-cli.svg?style=flat)](https://travis-ci.org/vmware/vca-cli/)

Command Line Interface for VMware vCloud Air. It supports vCloud Air (vCA & vCHS) and standalone vCloud Director.

This project is under development, the commands and parameters might change over time. This README usually reflects the syntax of the latest version. More information about commands and usage can be found in the [vca-cli wiki](https://github.com/vmware/vca-cli/wiki). See the [release notes](https://github.com/vmware/vca-cli/wiki/ReleaseNotes) for what's new.

`vca-cli` uses [pyvcloud](https://github.com/vmware/pyvcloud "Title"), Python SDK for VMware vCloud. 

Installation:
=============

In general, `vca-cli` can be installed with:

    $ pip install vca-cli

`vca-cli` requires a Python environment already installed, if the previous command fails, follow the instructions below.

Ubuntu:
-------

The following instructions have been tested with Ubuntu 12.04:

    $ sudo apt-get update
    
    $ sudo apt-get install -y build-essential libffi-dev libssl-dev \
                              libxml2-dev libxslt-dev python-dev
    
    $ wget https://bootstrap.pypa.io/get-pip.py
    
    $ sudo python get-pip.py
    
    $ sudo pip install vca-cli

Mac OS X:
---------

On Mac OS X (10.10.3), open a Terminal and enter the commands listed below (skip those that refer to a component already installed on your mac):

Install `Xcode Command Line Tools`:

    $ xcode-select --install    

Press `Install` and accept the license terms.

Install `pip`:

    $ sudo easy_install pip

Install `vca-cli`

    $ sudo -H pip install vca-cli

Verify Installation:
--------------------

Display the version installed:

    $ vca --version
    
    vca-cli version 14 (pyvcloud: 14)

Installation with virtualenv:
-----------------------------

It is also possible to install vca-cli in a [virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/).

Upgrade:
--------

To upgrade an existing `vca-cli` install, just run:

    $ pip install vca-cli --upgrade

You might need to run the previous command with `sudo` (on Ubuntu, CentOS and Mac OS) if not using `virtualenv`.

Pre-releases:
-------------

The commands described above install the current stable version of `vca-cli`. To install a pre-release version, enter:

    $ pip install vca-cli --pre

And to upgrade a pre-release:

    $ pip install vca-cli --pre --upgrade

You might need to run the previous command with `sudo` on Ubuntu and CentOS, if not using `virtualenv`.

SSL warnings:
------------

In some cases, it is necessary to install additional packages to avoid SSL warnings:

    $ sudo pip install pyopenssl ndg-httpsclient pyasn1

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

    $ vca example
    vca-cli usage examples:
    |   Id | Example                                      | Flavor     | Command                                                                                                                                                         |
    |------+----------------------------------------------+------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
    |    1 | login to service                             | vCA        | vca login email@company.com --password ****                                                                                                                     |
    |    2 | login to an instance                         | vCA        | vca login email@company.com --password **** --instance c40ba6b4-c158-49fb-b164-5c66f90344fa                                                                     |
    |    3 | login to a virtual data center               | vCA        | vca login email@company.com --password **** --instance c40ba6b4-c158-49fb-b164-5c66f90344fa --vdc VDC1                                                          |
    |    4 | login to service                             | vCHS       | vca login email@company.com --password **** --host vchs.vmware.com --version 5.6                                                                                |
    |    5 | login to an instance                         | vCHS       | vca login email@company.com --password **** --host vchs.vmware.com --version 5.6 --instance 55-234 --org MyOrg                                                  |
    |    6 | login to a virtual data center               | vCHS       | vca login email@company.com --password **** --host vchs.vmware.com --version 5.6 --instance 55-234 --org MyOrg --vdc MyVDC                                      |
    |    7 | login to vCloud Director                     | Standalone | vca login email@company.com --password **** --host myvcloud.company.com --version 5.5 --org MyOrg                                                               |
    |    8 | login to vCloud Director and VDC             | Standalone | vca login email@company.com --password **** --host myvcloud.company.com --version 5.5 --org MyOrg --vdc MyVDC                                                   |
    |    9 | use service with insecure SSL certs          | All        | vca --insecure login email@company.com --password **** --host myvcloud.company.com --version 5.5 --org MyOrg                                                    |
    |   10 | list available instances                     | vCA, vCHS  | vca instance                                                                                                                                                    |
    |   11 | show details of instance                     | vCA, vCHS  | vca instance info --instance c40ba6b4-c158-49fb-b164-5c66f90344fa                                                                                               |
    |   12 | select an instance                           | vCA        | vca instance use --instance c40ba6b4-c158-49fb-b164-5c66f90344fa                                                                                                |
    |   13 | select an instance and VDC                   | vCA        | vca instance use --instance c40ba6b4-c158-49fb-b164-5c66f90344fa --vdc MyVDC                                                                                    |
    |   14 | select an instance                           | vCHS       | vca instance use --instance M684216431-4470 --org M684216431-4470                                                                                               |
    |   15 | list organizations                           | All        | vca org                                                                                                                                                         |
    |   16 | show organization details                    | All        | vca org info                                                                                                                                                    |
    |   17 | select an organization                       | vCHS       | vca org use --instance 55-234 --org MyOrg                                                                                                                       |
    |   18 | list VDC templates                           | All        | vca org list-templates                                                                                                                                          |
    |   19 | list VDC                                     | All        | vca vdc                                                                                                                                                         |
    |   20 | select VDC                                   | All        | vca vdc use --vdc vdc1                                                                                                                                          |
    |   21 | create VDC                                   | All        | vca vdc create --vdc vdc2 --template d2p3v29-new-tp                                                                                                             |
    |   22 | delete VDC (will prompt to confirm)          | All        | vca vdc delete --vdc vdc2                                                                                                                                       |
    |   23 | delete VDC without prompt                    | All        | vca vdc delete --vdc vdc2 --yes                                                                                                                                 |
    |   24 | list catalogs and items                      | All        | vca catalog                                                                                                                                                     |
    |   25 | create catalog                               | All        | vca catalog create --catalog mycatalog                                                                                                                          |
    |   26 | delete catalog                               | All        | vca catalog delete --catalog mycatalog                                                                                                                          |
    |   27 | delete catalog item                          | All        | vca catalog delete-item --catalog mycatalog --item my_vapp_template                                                                                             |
    |   28 | upload media file (ISO) to catalog           | All        | vca catalog upload --catalog mycatalog --item esxi.iso --description ESXi-iso --file ~/VMware-VMvisor.iso                                                       |
    |   29 | list vApps                                   | All        | vca vapp                                                                                                                                                        |
    |   30 | create vApp                                  | All        | vca vapp create --vapp myvapp --vm myvm --catalog 'Public Catalog' --template 'Ubuntu Server 12.04 LTS (amd64 20150127)'                                        |
    |   31 | create vApp                                  | All        | vca vapp create -a myvapp -V myvm -c mycatalog -t mytemplate -n default-routed-network -m pool                                                                  |
    |   32 | create vApp with manually assigned IP        | All        | vca vapp create -a myvapp -V myvm -c mycatalog -t mytemplate -n default-routed-network -mode manual --ip 192.168.109.25                                         |
    |   33 | create multiple vApps                        | All        | vca vapp create -a myvapp -V myvm -c mycatalog -t mytemplate -n default-routed-network -m pool --count 10                                                       |
    |   34 | create vApp and configure VM size            | All        | vca vapp create -a myvapp -V myvm -c mycatalog -t mytemplate -n default-routed-network -m pool --cpu 4 --ram 4096                                               |
    |   35 | delete vApp                                  | All        | vca vapp delete --vapp myvapp                                                                                                                                   |
    |   36 | show vApp details in JSON                    | All        | vca -j vapp info --vapp myvapp                                                                                                                                  |
    |   37 | deploy vApp                                  | All        | vca vapp deploy --vapp ubu                                                                                                                                      |
    |   38 | undeploy vApp                                | All        | vca vapp undeploy --vapp ubu                                                                                                                                    |
    |   39 | power on vApp                                | All        | vca vapp power-on --vapp ubu                                                                                                                                    |
    |   40 | power off vApp                               | All        | vca vapp power-off --vapp ubu                                                                                                                                   |
    |   41 | customize vApp VM                            | All        | vca vapp customize --vapp ubu --vm ubu --file add_public_ssh_key.sh                                                                                             |
    |   42 | insert ISO to vApp VM                        | All        | vca vapp insert --vapp coreos1 --vm coreos1 --catalog default-catalog --media coreos1-config.iso                                                                |
    |   43 | eject ISO from vApp VM                       | All        | vca vapp eject --vapp coreos1 --vm coreos1 --catalog default-catalog --media coreos1-config.iso                                                                 |
    |   44 | attach disk to vApp VM                       | All        | vca vapp attach --vapp myvapp --vm myvm --disk mydisk                                                                                                           |
    |   45 | detach disk from vApp VM                     | All        | vca vapp detach --vapp myvapp --vm myvm --disk mydisk                                                                                                           |
    |   46 | list independent disks                       | All        | vca disk                                                                                                                                                        |
    |   47 | create independent disk of 100GB             | All        | vca disk create --disk mydisk --size 100                                                                                                                        |
    |   48 | delete independent disk by name              | All        | vca disk delete --disk mydisk                                                                                                                                   |
    |   49 | delete independent disk by id                | All        | vca disk delete --id bce76ca7-29d0-4041-82d4-e4481804d5c4                                                                                                       |
    |   50 | list VMs                                     | All        | vca vm                                                                                                                                                          |
    |   51 | list VMs in a vApp                           | All        | vca vm -a ubu                                                                                                                                                   |
    |   52 | list VMs in JSON format                      | All        | vca -j vm                                                                                                                                                       |
    |   53 | retrieve the IP of a VM                      | All        | IP=`vca -j vm -a ubu | jq -r '.vms[0].IPs[0]'` && echo $IP                                                                                                      |
    |   54 | list networks                                | All        | vca network                                                                                                                                                     |
    |   55 | create network                               | All        | vca network create --network net-117 --gateway-ip 192.168.117.1 --netmask 255.255.255.0 --dns1 8.8.8.8 --pool 192.168.117.2-192.168.117.100                     |
    |   56 | delete network                               | All        | vca network delete --network net-117                                                                                                                            |
    |   57 | list edge gateways                           | All        | vca gateway                                                                                                                                                     |
    |   58 | get details of edge gateway                  | All        | vca gateway info                                                                                                                                                |
    |   59 | set syslog server on gateway                 | All        | vca gateway set-syslog --ip 192.168.109.2                                                                                                                       |
    |   60 | unset syslog server on gateway               | All        | vca gateway set-syslog                                                                                                                                          |
    |   61 | allocate external IP address                 | vCA        | vca gateway add-ip                                                                                                                                              |
    |   62 | release external IP address                  | vCA        | vca gateway del-ip --ip 107.189.93.162                                                                                                                          |
    |   63 | list edge gateway firewall rules             | All        | vca firewall                                                                                                                                                    |
    |   64 | enable edge gateway firewall                 | All        | vca firewall enable                                                                                                                                             |
    |   65 | disable edge gateway firewall                | All        | vca firewall disable                                                                                                                                            |
    |   66 | add edge gateway firewall rule               | All        | vca firewall add --protocol tcp --dest-port 123 --dest-ip any --source-port 456 --source-ip any --description 'My awesome rule'                                 |
    |   67 | delete edge gateway firewall rule            | All        | vca firewall delete --protocol tcp --dest-port 123 --dest-ip any --source-port 456 --source-ip any                                                              |
    |   68 | add edge gateway firewall rules from file    | All        | vca firewall add --file fwrules.yaml                                                                                                                            |
    |   69 | delete edge gateway firewall rules from file | All        | vca firewall delete --file fwrules.yaml                                                                                                                         |
    |   70 | enable DHCP service                          | All        | vca dhcp enable                                                                                                                                                 |
    |   71 | disable DHCP service                         | All        | vca dhcp disable                                                                                                                                                |
    |   72 | add DHCP service to a network                | All        | vca dhcp add --network net-117 --pool 192.168.117.101-192.168.117.200                                                                                           |
    |   73 | remove DHCP service from a network           | All        | vca dhcp delete --network net-117                                                                                                                               |
    |   74 | list edge gateway NAT rules                  | All        | vca nat                                                                                                                                                         |
    |   75 | add edge gateway DNAT rule                   | All        | vca nat add --type dnat --original-ip 107.189.93.162 --original-port 22 --translated-ip 192.168.109.2 --translated-port 22 --protocol tcp                       |
    |   76 | add edge gateway SNAT rule                   | All        | vca nat add --type snat --original-ip 192.168.109.0/24 --translated-ip 107.189.93.162                                                                           |
    |   77 | add SNAT rule to network                     | All        | vca nat add --type snat --original-ip 192.168.109.0/24 --translated-ip 107.189.93.162 --network net-109                                                         |
    |   78 | add edge gateway NAT rules from file         | All        | vca nat add --file natrules.yaml                                                                                                                                |
    |   79 | delete edge gateway NAT rule                 | All        | vca nat delete --type dnat  --original-ip 107.189.93.162 --original-port 22 --translated-ip 192.168.109.4 --translated-port 22 --protocol tcp                   |
    |   80 | delete all edge gateway NAT rules            | All        | vca nat delete --all                                                                                                                                            |
    |   81 | list edge gateway VPN config                 | All        | vca vpn                                                                                                                                                         |
    |   82 | enable edge gateway VPN                      | All        | vca vpn enable                                                                                                                                                  |
    |   83 | disable edge gateway VPN                     | All        | vca vpn disable                                                                                                                                                 |
    |   84 | add VPN endpoint                             | All        | vca vpn add-endpoint --network d1p10-ext --public-ip 107.189.123.101                                                                                            |
    |   85 | delete VPN endpoint                          | All        | vca vpn del-endpoint --network d1p10-ext --public-ip 107.189.123.101                                                                                            |
    |   86 | add VPN tunnel                               | All        | vca vpn add-tunnel --tunnel t1 --local-ip 107.189.123.101 --local-network net-116 --peer-ip 192.240.158.15 --peer-network 192.168.110.0/24  --secret P8s3P...7v |
    |   87 | delete VPN tunnel                            | All        | vca vpn del-tunnel --tunnel t1                                                                                                                                  |
    |   88 | add local network to VPN tunnel              | All        | vca vpn add-network --tunnel t1 --local-network net-115                                                                                                         |
    |   89 | add peer network to VPN tunnel               | All        | vca vpn add-network --tunnel t1 --peer-network 192.168.117.0/24                                                                                                 |
    |   90 | delete local network from VPN tunnel         | All        | vca vpn del-network --tunnel t1 --local-network net-115                                                                                                         |
    |   91 | delete peer network from VPN tunnel          | All        | vca vpn del-network --tunnel t1 --peer-network 192.168.117.0/24                                                                                                 |
    |   92 | list user roles                              | vCA        | vca role                                                                                                                                                        |
    |   93 | list users                                   | vCA        | vca user                                                                                                                                                        |
    |   94 | change current user password                 | vCA        | vca user change-password --password current-pass --new-password new-pass                                                                                        |
    |   95 | create user                                  | vCA        | vca user create --user usr@com.com --first Name --last Name --roles 'Virtual Infrastructure Administrator, Network Administrator'                               |
    |   96 | delete user                                  | vCA        | vca user delete --id 65737432-9159-418b-945d-e10264130ccb                                                                                                       |
    |   97 | reset user password                          | vCA        | vca user reset-password --id 65737432-9159-418b-945d-e10264130ccb                                                                                               |
    |   98 | list blueprints                              | vCA        | vca blueprint                                                                                                                                                   |
    |   99 | validate blueprint                           | vCA        | vca blueprint validate --file helloworld/blueprint.yaml                                                                                                         |
    |  100 | upload blueprint                             | vCA        | vca blueprint upload --blueprint helloworld --file helloworld/blueprint.yaml                                                                                    |
    |  101 | show details of a blueprint                  | vCA        | vca blueprint info --blueprint helloworld                                                                                                                       |
    |  102 | delete blueprint                             | vCA        | vca blueprint delete --blueprint helloworld                                                                                                                     |
    |  103 | create deployment                            | vCA        | vca deployment create --blueprint helloworld --deployment d1 --file inputs.yaml                                                                                 |
    |  103 | list deployments                             | vCA        | vca deployment                                                                                                                                                  |
    |  104 | show details of a deployment                 | vCA        | vca deployment info --deployment d1                                                                                                                             |
    |  105 | execute deployment workflow                  | vCA        | vca deployment execute --deployment d1 --workflow install                                                                                                       |
    |  106 | delete deployment                            | vCA        | vca deployment delete --deployment d1                                                                                                                           |
    |  107 | list workflow execution events               | vCA        | vca event list --id f98df6cf-08d8-47fa-947f-67c15337efae                                                                                                        |
    |  108 | list workflow execution events               | vCA        | vca event list --id f98df6cf-08d8-47fa-947f-67c15337efae --show-logs                                                                                            |
    |  109 | show status                                  | All        | vca status                                                                                                                                                      |
    |  110 | show status and password                     | All        | vca status --show-password                                                                                                                                      |
    |  111 | list profiles                                | All        | vca profile                                                                                                                                                     |
    |  112 | switch to a profile                          | All        | vca --profile p1 <command>                                                                                                                                      |
    |  113 | send debug to $TMPDIR/pyvcloud.log           | All        | vca --debug vm                                                                                                                                                  |
    |  114 | show version                                 | All        | vca --version                                                                                                                                                   |
    |  115 | show general help                            | All        | vca --help                                                                                                                                                      |
    |  116 | show command help                            | All        | vca <command> --help                                                                                                                                            |

Syntax, commands and arguments:

    
    $ vca --help
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

Detailed syntax for a specific command:

    
    $ vca vapp --help
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
