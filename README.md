vca-cli
=======

Command Line Interface for VMware vCloud Air. It supports vCloud Air On Demand and Subscription. It also supports vCloud Director.

> Release early, release often.

This project is under development, the commands and parameters might change over time. This README usually reflects the syntax of the latest version. See the [documentation](http://vca-cli.readthedocs.org) for a detailed description of each command. More information about commands and usage can be found in the [vca-cli wiki](https://github.com/vmware/vca-cli/wiki). The [networking section](https://github.com/vmware/vca-cli/wiki/Networking) documents all the operations related to networks, edge gateway and network services.

vca-cli uses [pyvcloud](https://github.com/vmware/pyvcloud "Title"), Python SDK for VMware vCloud. 

Installation:
=============

    
    $ pip install vca-cli
    

The vca-cli requires a Python environment installed, if the previous command fails, install the dependencies. Here is an example of installing the dependencies on Debian/Ubuntu:

    
    $ sudo apt-get install -y build-essential libssl-dev libffi-dev libxml2-dev libxslt-dev python-dev python-pip
    
    $ sudo pip install vca-cli
    

On MacOS, download and install the latest [Xcode command line tools](https://developer.apple.com/xcode/downloads/) and [Homebrew](http://brew.sh), then:

    
    $ brew install libxml2
    

It is also possible to install vca-cli in a [virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/)

Upgrade from a previous installation:

        
    $ pip install vca-cli --upgrade
    

Install completions for oh-my-zsh

    
    $ wget https://raw.githubusercontent.com/vmware/vca-cli/master/scripts/_vca -O ~/.oh-my-zsh/completions/_vca
    

Usage:
======

Login. When the *password* argument is omitted, vca-cli will prompt the user for the password:

    
    # vCA On Demand, password prompt
    vca login user@domain.com
    Password: ***************
    
    # vCA On Demand
    $ vca login user@domain.com --password ********
    
    # same as:
    $ vca login user@domain.com --password ******** --host iam.vchs.vmware.com --type ondemand --version 5.7
    
    # vCA Subscription
    $ vca login user@domain.com --password ******** --host vchs.vmware.com --type subscription --version 5.6
    
    # vCloud Director
    $ vca login user@domain.com --password ******** --host vcdhost.domain.com --org myorg --type vcd --version 5.6
    
    # vCloud Director with insecure SSL certificate
    $ vca --insecure login user@domain.com --password ******** --host vcdhost.domain.com --org myorg --type vcd --version 5.6
    

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
    | Property        | Value                                                |
    |-----------------+------------------------------------------------------|
    | gateway         |                                                      |
    | host            | https://iam.vchs.vmware.com                          |
    | instance        | c40ba6b4-c158-49fb-b164-5c66f90344fa                 |
    | org             | a6545fcb-d68a-489f-afff-2ea055104cc1                 |
    | org_url         | https://us-california-1-3.vchs.vmware.com/api/comp.. |
    | service         |                                                      |
    | service_type    | ondemand                                             |
    | service_version | 5.7                                                  |
    | session         | active                                               |
    | session_token   | 1135106472314155bea13eb60d8198c6                     |
    | token           | eyJhbGciOiJSUzI1NiJ9.eyJqdGkiOiJlZmJlODhiZi03YjZjL.. |
    | user            | email@company.com                                    |
    | vdc             | VDC1                                                 |
    

Logout:

    
    $ vca logout
    Logout successful for profile 'default'
    

Usage examples:

    
    $ vca example
    |   Id | Example                                    | Command                                                                                                                                                                                  |
    |------+--------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
    |    1 | login to vCA On Demand                     | vca login email@company.com --password mypassword                                                                                                                                        |
    |    2 | login to a vCA On Demand instance          | vca login email@company.com --password mypassword --instance c40ba6b4-c158-49fb-b164-5c66f90344fa                                                                                        |
    |    3 | login to vCA Subscription                  | vca login email@company.com --password mypassword --type subscription --host https://vchs.vmware.com --version 5.6                                                                       |
    |    4 | login to vCloud Director                   | vca login email@company.com --password mypassword --type vcd --host https://p1v21-vcd.vchs.vmware.com --version 5.6 --org MyOrganization                                                 |
    |    5 | login with no SSL verification             | vca --insecure login email@company.com --password mypassword                                                                                                                             |
    |    6 | prompt user for password                   | vca login email@company.com                                                                                                                                                              |
    |    7 | show status                                | vca status                                                                                                                                                                               |
    |    8 | logout                                     | vca logout                                                                                                                                                                               |
    |    9 | list organizations                         | vca org                                                                                                                                                                                  |
    |   10 | select organization                        | vca org use --org MyOrg                                                                                                                                                                  |
    |   11 | select organization in subscription        | vca org use --org MyOrg --service ServiceId                                                                                                                                              |
    |   12 | show current organization                  | vca org info                                                                                                                                                                             |
    |   13 | select and show organization               | vca org info --org MyOrg                                                                                                                                                                 |
    |   14 | show current organization in XML           | vca --xml org info                                                                                                                                                                       |
    |   15 | show current organization in JSON          | vca --json org info                                                                                                                                                                      |
    |   16 | list virtual data centers                  | vca vdc                                                                                                                                                                                  |
    |   17 | select virtual data centers                | vca vdc use --vdc VDC1                                                                                                                                                                   |
    |   18 | show virtual data center                   | vca vdc info                                                                                                                                                                             |
    |   19 | list catalogs                              | vca catalog                                                                                                                                                                              |
    |   20 | create catalog                             | vca catalog create --catalog mycatalog                                                                                                                                                   |
    |   21 | delete catalog                             | vca catalog delete --catalog mycatalog                                                                                                                                                   |
    |   22 | delete catalog item                        | vca catalog delete-item --catalog mycatalog --item my_vapp_template                                                                                                                      |
    |   23 | list networks                              | vca network                                                                                                                                                                              |
    |   24 | list vapps                                 | vca vapp                                                                                                                                                                                 |
    |   25 | create vapp                                | vca vapp create -a coreos2 -V coreos2 -c default-catalog -t coreos_template -n default-routed-network -m pool                                                                            |
    |   26 | create vapp                                | vca vapp create --vapp myvapp --vm myvm --catalog 'Public Catalog' --template 'Ubuntu Server 12.04 LTS (amd64 20150127)' --network default-routed-network --mode POOL                    |
    |   27 | create multiple vapps                      | vca vapp create --vapp myvapp --vm myvm --catalog 'Public Catalog' --template 'Ubuntu Server 12.04 LTS (amd64 20150127)' --network default-routed-network --mode POOL --count 10         |
    |   28 | create vapp and configure vm size          | vca vapp create --vapp myvapp --vm myvm --catalog 'Public Catalog' --template 'Ubuntu Server 12.04 LTS (amd64 20150127)' --network default-routed-network --mode POOL --cpu 4 --ram 4096 |
    |   29 | delete vapp                                | vca vapp delete -a coreos2                                                                                                                                                               |
    |   30 | show vapp details in XML                   | vca -x vapp info -a coreos2                                                                                                                                                              |
    |   31 | deploy vapp                                | vca vapp deploy --vapp ubu                                                                                                                                                               |
    |   32 | undeploy vapp                              | vca vapp undeploy --vapp ubu                                                                                                                                                             |
    |   33 | customize vapp vm                          | vca vapp customize --vapp ubu --vm ubu --file add_public_ssh_key.sh                                                                                                                      |
    |   34 | insert ISO to vapp vm                      | vca vapp insert --vapp coreos1 --vm coreos1 --catalog default-catalog --media coreos1-config.iso                                                                                         |
    |   35 | eject ISO from vapp vm                     | vca vapp eject --vapp coreos1 --vm coreos1 --catalog default-catalog --media coreos1-config.iso                                                                                          |
    |   36 | attach disk to vapp vm                     | vca vapp attach --vapp myvapp --vm myvm --disk mydisk                                                                                                                                    |
    |   37 | detach disk from vapp vm                   | vca vapp detach --vapp myvapp --vm myvm --disk mydisk                                                                                                                                    |
    |   38 | list independent disks                     | vca vapp disk                                                                                                                                                                            |
    |   39 | create independent disk of 100GB           | vca vapp disk create --disk mydisk --size 100                                                                                                                                            |
    |   40 | delete independent disk by name            | vca vapp disk delete --disk mydisk                                                                                                                                                       |
    |   41 | delete independent disk by id              | vca vapp disk delete --id bce76ca7-29d0-4041-82d4-e4481804d5c4                                                                                                                           |
    |   42 | list vms                                   | vca vm                                                                                                                                                                                   |
    |   43 | list vms in a vapp                         | vca vm -a ubu                                                                                                                                                                            |
    |   44 | list vms in JSON format                    | vca -j vm                                                                                                                                                                                |
    |   45 | retrieve the IP of a vm                    | IP=`vca -j vm -a ubu | jq -r '.vms[0].IPs[0]'` && echo $IP                                                                                                                               |
    |   46 | list networks                              | vca network                                                                                                                                                                              |
    |   47 | create network                             | vca network create --network network_name --gateway gateway_name --gateway-ip 192.168.117.1 --netmask 255.255.255.0 --dns1 192.168.117.1 --pool 192.168.117.2-192.168.117.100            |
    |   48 | delete network                             | vca network delete --network network_name                                                                                                                                                |
    |   49 | list edge gateways                         | vca gateway                                                                                                                                                                              |
    |   50 | get details of edge gateways               | vca gateway info --gateway gateway_name                                                                                                                                                  |
    |   51 | set syslog server on gateway               | vca gateway set-syslog --gateway gateway_name --ip 192.168.109.2                                                                                                                         |
    |   52 | unset syslog server on gateway             | vca gateway set-syslog --gateway gateway_name                                                                                                                                            |
    |   53 | allocate external IP address in OnDemand   | vca gateway add-ip                                                                                                                                                                       |
    |   54 | deallocate external IP address in OnDemand | vca gateway del-ip --ip 107.189.93.162                                                                                                                                                   |
    |   55 | list edge gateway NAT rules                | vca nat                                                                                                                                                                                  |
    |   56 | add edge gateway DNAT rule                 | vca nat add --type DNAT --original-ip 107.189.93.162 --original-port 22 --translated-ip 192.168.109.2 --translated-port 22 --protocol tcp                                                |
    |   57 | add edge gateway SNAT rule                 | vca nat add --type SNAT --original-ip 192.168.109.0/24 --translated-ip 107.189.93.162                                                                                                    |
    |   58 | add edge gateway rules from file           | vca nat add --file natrules.yaml                                                                                                                                                         |
    |   59 | delete edge gateway NAT rule               | vca nat delete --type DNAT --original-ip 107.189.93.162 --original-port 22 --translated-ip 192.168.109.4 --translated-port 22 --protocol tcp                                             |
    |   60 | delete all edge gateway NAT rules          | vca nat delete --all                                                                                                                                                                     |
    |   61 | enable edge gateway firewall               | vca fw enable                                                                                                                                                                            |
    |   62 | disable edge gateway firewall              | vca fw disable                                                                                                                                                                           |
    |   63 | display DHCP configuration                 | vca dhcp                                                                                                                                                                                 |
    |   64 | enable DHCP service                        | vca dhcp enable                                                                                                                                                                          |
    |   65 | disable DHCP service                       | vca dhcp disable                                                                                                                                                                         |
    |   66 | add DHCP service to a network              | vca dhcp add --network routed-211 --pool 192.168.211.101-192.168.211.200                                                                                                                 |
    |   67 | delete all DHCP pools from a network       | vca dhcp delete --network routed-211                                                                                                                                                     |
    |   68 | list edge gateway VPN config               | vca vpn                                                                                                                                                                                  |
    |   69 | enable edge gateway VPN                    | vca vpn enable                                                                                                                                                                           |
    |   70 | disable edge gateway VPN                   | vca vpn disable                                                                                                                                                                          |
    |   71 | add VPN endpoint                           | vca vpn add-endpoint --network d1p10-ext --public-ip 107.189.123.101                                                                                                                     |
    |   72 | delete VPN endpoint                        | vca vpn del-endpoint --network d1p10-ext --public-ip 107.189.123.101                                                                                                                     |
    |   73 | add VPN tunnel                             | vca vpn add-tunnel --tunnel t1 --local-ip 107.189.123.101 --local-network routed-116 --peer-ip 192.240.158.15 --peer-network 192.168.110.0/24 --secret P8s3P...7v                        |
    |   74 | delete VPN tunnel                          | vca vpn del-tunnel --tunnel t1                                                                                                                                                           |
    |   75 | add local network to VPN tunnel            | vca vpn add-network --tunnel t1 --local-network routed-115                                                                                                                               |
    |   76 | add peer network to VPN tunnel             | vca vpn add-network --tunnel t1 --peer-network 192.168.115.0/24                                                                                                                          |
    |   77 | delete local network from VPN tunnel       | vca vpn del-network --tunnel t1 --local-network routed-115                                                                                                                               |
    |   78 | delete peer network from VPN tunnel        | vca vpn del-network --tunnel t1 --peer-network 192.168.115.0/24                                                                                                                          |
    |   79 | show the REST calls in the command         | vca --debug vm                                                                                                                                                                           |
    |   80 | show version                               | vca --version                                                                                                                                                                            |
    |   81 | show help                                  | vca --help                                                                                                                                                                               |
    |   82 | show command help                          | vca <command> --help                                                                                                                                                                     |

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

    
    $vca vapp --help
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
      

