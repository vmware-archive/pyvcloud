vca-cli
=======

[![Download Status](https://img.shields.io/pypi/dm/vca-cli.svg)](https://pypi.python.org/pypi/vca-cli) [![Stable Version](https://img.shields.io/pypi/v/vca-cli.svg)](https://pypi.python.org/pypi/vca-cli) [![Build Status](https://img.shields.io/travis/vmware/vca-cli.svg?style=flat)](https://travis-ci.org/vmware/vca-cli/)

NOTE: due to changes in the service, use the --host argument to login on OnDemand:

    $ vca login user@company.com --host vca.vmware.com --password $PASS --save-password

Command Line Interface for VMware vCloud Air. It supports vCloud Air On Demand and Subscription. It also supports standalone vCloud Director.

> Release early, release often.

This project is under development, the commands and parameters might change over time. This README usually reflects the syntax of the latest version. See the [documentation](http://vca-cli.readthedocs.org) for a detailed description of each command. More information about commands and usage can be found in the [vca-cli wiki](https://github.com/vmware/vca-cli/wiki). The [networking section](https://github.com/vmware/vca-cli/wiki/Networking) documents all the operations related to networks, edge gateway and network services. See the [release notes](https://github.com/vmware/vca-cli/wiki/ReleaseNotes) for what's new.

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

    $ sudo pip install vca-cli

Verify Installation:
--------------------

Display the version installed:

    $ vca --version
    
    vca-cli version 12 (pyvcloud: 13)

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

Usage:
======

Login and Logout:
-----------------

When the *password* argument is omitted, `vca-cli` will prompt the user for the password. Use the `--save-password` to cache the password (encrypted) and automatically re-login when the token expires. Below are some examples:

    
    # vCA On Demand, password prompt
    vca login user@domain.com
    Password: ***************
    
    # vCA On Demand
    $ vca login user@domain.com --password ******** --save-password
    
    # same as:
    $ vca login user@domain.com --password ******** --save-password \
             --host iam.vchs.vmware.com --type ondemand --version 5.7
    
    # vCA Subscription
    $ vca login user@domain.com --password ******** --save-password \
             --host vchs.vmware.com --type subscription --version 5.6
    
    # vCloud Director Standalone
    $ vca login user@domain.com --password ******** --save-password \
             --host vcdhost.domain.com --org myorg --type standalone --version 5.6
    
    # vCloud Director with insecure SSL certificate
    $ vca login user@domain.com --password ******** --save-password \
             --host vcdhost.domain.com --org myorg --type standalone --version 5.6 \
             --insecure

vCloud Air On Demand, login to a specific instance and get the details of the instance (organization):

    
    $ vca login user@domain.com --password ********
    Login successful for profile 'default'
    
    $ vca instance
    Available instances for user 'email@company.com' in 'default' profile:
    | Instance Id                          | Region                            | Plan Id                              |
    |--------------------------------------+-----------------------------------+--------------------------------------|
    | fbf278f0-065d-4028-96d4-6ece56789751 | us-virginia-1-4.vchs.vmware.com   | feda2919-32cb-4efd-a4e5-c5953733df33 |
    | c40ba6b4-c158-49fb-b164-5c66f90344fa | us-california-1-3.vchs.vmware.com | 41400e74-4445-49ef-90a4-98da4ccfb16c |
    | 7d275413-bc0b-4bbf-8c7b-b9522777beec | uk-slough-1-6.vchs.vmware.com     | 62155213-e5fc-448d-a46a-770c57c5dd31 |
    
    $ vca login user@domain.com --password ******** --instance c40ba6b4-c158-49fb-b164-5c66f90344fa
    Login successful for profile 'default'
    
    $ vca org info
    Details for org 'a6545fcb-d68a-489f-afff-2ea055104cc1':
    | Type       | Name                   |
    |------------+------------------------|
    | catalog    | Public Catalog         |
    | catalog    | default-catalog        |
    | orgNetwork | default-routed-network |
    | orgNetwork | default-routed-network |
    | vdc        | VDC1                   |
    | vdc        | VDC2                   |
    

Connection status:

    
    $ vca status
    
    Status:
    | Property         | Value                                                |
    |------------------+------------------------------------------------------|
    | gateway          |                                                      |
    | host             | https://iam.vchs.vmware.com                          |
    | host_score       | https://score.vca.io                                 |
    | instance         | d7a623de-1183-46a9-9b02-9043ca68f441                 |
    | org              |                                                      |
    | org_url          | https://us-virginia-1-4.vchs.vmware.com/api/comput.. |
    | password         | <encrypted>                                          |
    | pyvcloud_version | 13rc14                                               |
    | service          | 85-719                                               |
    | service_type     | ondemand                                             |
    | service_version  | 5.7                                                  |
    | session          | active                                               |
    | session_token    | 523823d5754f43ad85cbb72333e8343b                     |
    | session_uri      | https://us-virginia-1-4.vchs.vmware.com/api/comput.. |
    | token            | eyJhbGciOiJSUzI1NiJ9.eyJqdGkiOiI2MzVlZGQ4Ni1iMTNhL.. |
    | user             | vca_sas_oda@vmware.com                               |
    | vca_cli_version  | 12rc9                                                |
    | vdc              | vdc-tmp                                              |
    | verify           | True                                                 |

Logout:

    
    $ vca logout
    Logout successful for profile 'default'
    

Examples and Help:
------------------

`vca-cli` provides a list of examples with the `example` command:

    $ vca example
    
    vca-cli usage examples:
    |   Id | Example                                 | Command                                                                                                                                                                                     |
    |------+-----------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
    |    1 | login to vCA On Demand                  | vca login email@company.com --password mypassword --save-password                                                                                                                           |
    |    2 | login to a vCA On Demand instance       | vca login email@company.com --password mypassword --save-password --instance c40ba6b4-c158-49fb-b164-5c66f90344fa                                                                           |
    |    3 | login to vCA Subscription               | vca login email@company.com --password mypassword --save-password --type subscription --host https://vchs.vmware.com --version 5.6                                                          |
    |    4 | login to vCloud Director standalone     | vca login email@company.com --password mypassword --save-password --type standalone --host https://p1v21-vcd.vchs.vmware.com --version 5.6 --org MyOrganization                             |
    |    5 | login with no SSL verification          | vca --insecure login email@company.com --password mypassword --save-password                                                                                                                |
    |    6 | prompt user for password                | vca login email@company.com --save-password                                                                                                                                                 |
    |    7 | show status                             | vca status                                                                                                                                                                                  |
    |    8 | logout                                  | vca logout                                                                                                                                                                                  |
    |    9 | list organizations                      | vca org                                                                                                                                                                                     |
    |   10 | select organization                     | vca org use --org MyOrg                                                                                                                                                                     |
    |   11 | select organization in subscription     | vca org use --org MyOrg --service ServiceId                                                                                                                                                 |
    |   12 | show current organization               | vca org info                                                                                                                                                                                |
    |   13 | select and show organization            | vca org info --org MyOrg                                                                                                                                                                    |
    |   14 | show current organization in XML        | vca --xml org info                                                                                                                                                                          |
    |   15 | show current organization in JSON       | vca --json org info                                                                                                                                                                         |
    |   16 | list virtual data centers               | vca vdc                                                                                                                                                                                     |
    |   17 | select virtual data centers             | vca vdc use --vdc VDC1                                                                                                                                                                      |
    |   18 | show virtual data center                | vca vdc info                                                                                                                                                                                |
    |   19 | list catalogs                           | vca catalog                                                                                                                                                                                 |
    |   20 | create catalog                          | vca catalog create --catalog mycatalog                                                                                                                                                      |
    |   21 | delete catalog                          | vca catalog delete --catalog mycatalog                                                                                                                                                      |
    |   22 | delete catalog item                     | vca catalog delete-item --catalog mycatalog --item my_vapp_template                                                                                                                         |
    |   23 | upload media file (ISO) to catalog      | vca catalog upload --catalog mycatalog --item esxi.iso --description ESXi-iso --file ~/VMware-VMvisor.iso                                                                                   |
    |   24 | list networks                           | vca network                                                                                                                                                                                 |
    |   25 | list vapps                              | vca vapp                                                                                                                                                                                    |
    |   26 | create vapp                             | vca vapp create -a coreos2 -V coreos2 -c default-catalog -t coreos_template -n default-routed-network -m pool                                                                               |
    |   27 | create vapp                             | vca vapp create --vapp myvapp --vm myvm --catalog 'Public Catalog' --template 'Ubuntu Server 12.04 LTS (amd64 20150127)' --network default-routed-network --mode pool                       |
    |   28 | create vapp with manually assigned IP   | vca vapp create --vapp myvapp --vm myvm --catalog 'Public Catalog' --template 'Ubuntu Server 12.04 LTS (amd64 20150127)' --network default-routed-network --mode manual --ip 192.168.109.25 |
    |   29 | create multiple vapps                   | vca vapp create --vapp myvapp --vm myvm --catalog 'Public Catalog' --template 'Ubuntu Server 12.04 LTS (amd64 20150127)' --network default-routed-network --mode pool --count 10            |
    |   30 | create vapp and configure vm size       | vca vapp create --vapp myvapp --vm myvm --catalog 'Public Catalog' --template 'Ubuntu Server 12.04 LTS (amd64 20150127)' --network default-routed-network --mode pool --cpu 4 --ram 4096    |
    |   31 | delete vapp                             | vca vapp delete -a coreos2                                                                                                                                                                  |
    |   32 | show vapp details in XML                | vca -x vapp info -a coreos2                                                                                                                                                                 |
    |   33 | deploy vapp                             | vca vapp deploy --vapp ubu                                                                                                                                                                  |
    |   34 | undeploy vapp                           | vca vapp undeploy --vapp ubu                                                                                                                                                                |
    |   35 | customize vapp vm                       | vca vapp customize --vapp ubu --vm ubu --file add_public_ssh_key.sh                                                                                                                         |
    |   36 | insert ISO to vapp vm                   | vca vapp insert --vapp coreos1 --vm coreos1 --catalog default-catalog --media coreos1-config.iso                                                                                            |
    |   37 | eject ISO from vapp vm                  | vca vapp eject --vapp coreos1 --vm coreos1 --catalog default-catalog --media coreos1-config.iso                                                                                             |
    |   38 | attach disk to vapp vm                  | vca vapp attach --vapp myvapp --vm myvm --disk mydisk                                                                                                                                       |
    |   39 | detach disk from vapp vm                | vca vapp detach --vapp myvapp --vm myvm --disk mydisk                                                                                                                                       |
    |   40 | list independent disks                  | vca vapp disk                                                                                                                                                                               |
    |   41 | create independent disk of 100GB        | vca disk create --disk mydisk --size 100                                                                                                                                                    |
    |   42 | delete independent disk by name         | vca disk delete --disk mydisk                                                                                                                                                               |
    |   43 | delete independent disk by id           | vca disk delete --id bce76ca7-29d0-4041-82d4-e4481804d5c4                                                                                                                                   |
    |   44 | list vms                                | vca vm                                                                                                                                                                                      |
    |   45 | list vms in a vapp                      | vca vm -a ubu                                                                                                                                                                               |
    |   46 | list vms in JSON format                 | vca -j vm                                                                                                                                                                                   |
    |   47 | retrieve the IP of a vm                 | IP=`vca -j vm -a ubu | jq -r '.vms[0].IPs[0]'` && echo $IP                                                                                                                                  |
    |   48 | list networks                           | vca network                                                                                                                                                                                 |
    |   49 | create network                          | vca network create --network network_name --gateway gateway_name --gateway-ip 192.168.117.1 --netmask 255.255.255.0 --dns1 192.168.117.1 --pool 192.168.117.2-192.168.117.100               |
    |   50 | delete network                          | vca network delete --network network_name                                                                                                                                                   |
    |   51 | list edge gateways                      | vca gateway                                                                                                                                                                                 |
    |   52 | get details of edge gateways            | vca gateway info --gateway gateway_name                                                                                                                                                     |
    |   53 | set syslog server on gateway            | vca gateway set-syslog --gateway gateway_name --ip 192.168.109.2                                                                                                                            |
    |   54 | unset syslog server on gateway          | vca gateway set-syslog --gateway gateway_name                                                                                                                                               |
    |   55 | allocate external IP address (OnDemand) | vca gateway add-ip                                                                                                                                                                          |
    |   56 | release external IP address (OnDemand)  | vca gateway del-ip --ip 107.189.93.162                                                                                                                                                      |
    |   57 | list edge gateway NAT rules             | vca nat                                                                                                                                                                                     |
    |   58 | add edge gateway DNAT rule              | vca nat add --type DNAT --original-ip 107.189.93.162 --original-port 22 --translated-ip 192.168.109.2 --translated-port 22 --protocol tcp                                                   |
    |   59 | add edge gateway SNAT rule              | vca nat add --type SNAT --original-ip 192.168.109.0/24 --translated-ip 107.189.93.162                                                                                                       |
    |   60 | add edge gateway rules from file        | vca nat add --file natrules.yaml                                                                                                                                                            |
    |   61 | delete edge gateway NAT rule            | vca nat delete --type DNAT  --original-ip 107.189.93.162 --original-port 22 --translated-ip 192.168.109.4 --translated-port 22 --protocol tcp                                               |
    |   62 | delete all edge gateway NAT rules       | vca nat delete --all                                                                                                                                                                        |
    |   63 | enable edge gateway firewall            | vca firewall enable                                                                                                                                                                         |
    |   64 | disable edge gateway firewall           | vca firewall disable                                                                                                                                                                        |
    |   65 | display DHCP configuration              | vca dhcp                                                                                                                                                                                    |
    |   66 | enable DHCP service                     | vca dhcp enable                                                                                                                                                                             |
    |   67 | disable DHCP service                    | vca dhcp disable                                                                                                                                                                            |
    |   68 | add DHCP service to a network           | vca dhcp add --network routed-211 --pool 192.168.211.101-192.168.211.200                                                                                                                    |
    |   69 | delete all DHCP pools from a network    | vca dhcp delete --network routed-211                                                                                                                                                        |
    |   70 | list edge gateway VPN config            | vca vpn                                                                                                                                                                                     |
    |   71 | enable edge gateway VPN                 | vca vpn enable                                                                                                                                                                              |
    |   72 | disable edge gateway VPN                | vca vpn disable                                                                                                                                                                             |
    |   73 | add VPN endpoint                        | vca vpn add-endpoint --network d1p10-ext --public-ip 107.189.123.101                                                                                                                        |
    |   74 | delete VPN endpoint                     | vca vpn del-endpoint --network d1p10-ext --public-ip 107.189.123.101                                                                                                                        |
    |   75 | add VPN tunnel                          | vca vpn add-tunnel --tunnel t1 --local-ip 107.189.123.101 --local-network routed-116 --peer-ip 192.240.158.15 --peer-network 192.168.110.0/24  --secret P8s3P...7v                          |
    |   76 | delete VPN tunnel                       | vca vpn del-tunnel --tunnel t1                                                                                                                                                              |
    |   77 | add local network to VPN tunnel         | vca vpn add-network --tunnel t1 --local-network routed-115                                                                                                                                  |
    |   78 | add peer network to VPN tunnel          | vca vpn add-network --tunnel t1 --peer-network 192.168.115.0/24                                                                                                                             |
    |   79 | delete local network from VPN tunnel    | vca vpn del-network --tunnel t1 --local-network routed-115                                                                                                                                  |
    |   80 | delete peer network from VPN tunnel     | vca vpn del-network --tunnel t1 --peer-network 192.168.115.0/24                                                                                                                             |
    |   81 | send debug to $TMPDIR/pyvcloud.log      | vca --debug vm                                                                                                                                                                              |
    |   82 | show version                            | vca --version                                                                                                                                                                               |
    |   83 | show help                               | vca --help                                                                                                                                                                                  |
    |   84 | show command help                       | vca <command> --help                                                                                                                                                                        |

Syntax, commands and arguments:

    
    $ vca --help
    Usage: vca [OPTIONS] COMMAND [ARGS]...
    
      VMware vCloud Air Command Line Interface.
      
    Options:
      -p, --profile <profile>  Profile id
      -v, --version            Show version
      -d, --debug              Enable debug
      -j, --json               Results as JSON object
      -x, --xml                Results as XML document
      -i, --insecure           Perform insecure SSL connections
      -h, --help               Show this message and exit.
      
    Commands:
      bp        Operations with Blueprints
      catalog   Operations with Catalogs
      dep       Operations with Deployments
      dhcp      Operations with Edge Gateway DHCP Service
      example   vCloud Air CLI Examples
      firewall  Operations with Edge Gateway Firewall Rules
      gateway   Operations with Edge Gateway
      instance  Operations with Instances
      login     Login to a vCloud service
      logout    Logout from a vCloud service
      nat       Operations with Edge Gateway NAT Rules
      network   Operations with Networks
      org       Operations with Organizations
      plan      Operations with Instances
      status    Show current status
      vapp      Operations with vApps
      vdc       Operations with Virtual Data Centers (vdc)
      vm        Operations with Virtual Machines (VMs)
      vpn       Operations with Edge Gateway VPN
          

Detailed syntax for a specific command:

    $ vca vapp --help
    Usage: vca vapp [OPTIONS] [list | info | create | delete | power.on |
                    power.off | deploy | undeploy | customize |
                    insert | eject]
                    
      Operations with vApps
      
    Options:
      -v, --vdc <vdc>                 Virtual Data Center Id
      -a, --vapp <vapp>               vApp name
      -c, --catalog <catalog>         catalog name
      -t, --template <template>       template name
      -n, --network <network>         Network name
      -m, --mode [POOL, DHCP]         Network connection mode
      -V, --vm <vm>                   VM name
      -f, --file <customization_file>
                                      Guest OS Customization script file
      -e, --media <media>             virtual media name (ISO)
      -h, --help                      Show this message and exit.

