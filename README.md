vca-cli
=======

Command Line Interface for VMware vCloud Air. It supports vCloud Air On Demand and Subscription. It also supports vCloud Director.

> Release early, release often.

This project is under development, the commands and parameters might change over time. This README usually reflects the syntax of the latest version. Uses [pyvcloud](https://github.com/vmware/pyvcloud "Title"), Python SDK for VMware vCloud.

Installation:

    
    $ pip install vca-cli
    

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
    vca-cli usage examples:
    |   Id | Example                             | Command                                                                                                                                      |
    |------+-------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------|
    |    1 | login to vCA On Demand              | vca login email@company.com --password mypassword                                                                                            |
    |    2 | login to a vCA On Demand instance   | vca login email@company.com --password mypassword --instance c40ba6b4-c158-49fb-b164-5c66f90344fa                                            |
    |    3 | login to vCA Subscription           | vca login email@company.com --password mypassword --type subscription --host https://vchs.vmware.com --version 5.6                           |
    |    4 | login to vCloud Director            | vca login email@company.com --password mypassword --type vcd --host https://p1v21-vcd.vchs.vmware.com --version 5.6 --org MyOrganization     |
    |    5 | login with no SSL verification      | vca --insecure login email@company.com --password mypassword                                                                                 |
    |    6 | prompt user for password            | vca login email@company.com                                                                                                                  |
    |    7 | show status                         | vca status                                                                                                                                   |
    |    8 | logout                              | vca logout                                                                                                                                   |
    |    9 | list organizations                  | vca org                                                                                                                                      |
    |   10 | select organization                 | vca org use --org MyOrg                                                                                                                      |
    |   11 | select organization in subscription | vca org use --org MyOrg --service ServiceId                                                                                                  |
    |   12 | show current organization           | vca org info                                                                                                                                 |
    |   13 | select and show organization        | vca org info --org MyOrg                                                                                                                     |
    |   14 | show current organization in XML    | vca --xml org info                                                                                                                           |
    |   15 | show current organization in JSON   | vca --json org info                                                                                                                          |
    |   16 | list virtual data centers           | vca vdc                                                                                                                                      |
    |   17 | select virtual data centers         | vca vdc use --vdc VDC1                                                                                                                       |
    |   18 | show virtual data center            | vca vdc info                                                                                                                                 |
    |   19 | list catalogs                       | vca catalog                                                                                                                                  |
    |   20 | create catalog                      | vca catalog create --catalog mycatalog                                                                                                       |
    |   21 | delete catalog                      | vca catalog delete --catalog mycatalog                                                                                                       |
    |   22 | list networks                       | vca network                                                                                                                                  |
    |   23 | list vapps                          | vca vapp                                                                                                                                     |
    |   24 | create vapp                         | vca vapp create -a coreos2 -V coreos2 -c default-catalog -t coreos_template -n default-routed-network -m POOL                                |
    |   25 | delete vapp                         | vca vapp delete -a coreos2                                                                                                                   |
    |   26 | show vapp details in XML            | vca -x vapp info -a coreos2                                                                                                                  |
    |   27 | deploy vapp                         | vca vapp deploy --vapp ubu                                                                                                                   |
    |   28 | undeploy vapp                       | vca vapp undeploy --vapp ubu                                                                                                                 |
    |   29 | customize vapp vm                   | vca vapp customize --vapp ubu --vm ubu --file add_public_ssh_key.sh                                                                          |
    |   30 | insert ISO to vapp vm               | vca vapp insert --vapp coreos1 --vm coreos1 --catalog default-catalog --media coreos1-config.iso                                             |
    |   31 | eject ISO from vapp vm              | vca vapp eject --vapp coreos1 --vm coreos1 --catalog default-catalog --media coreos1-config.iso                                              |
    |   32 | list vms                            | vca vm                                                                                                                                       |
    |   33 | list vms in a vapp                  | vca vm -a ubu                                                                                                                                |
    |   34 | list vms in JSON format             | vca -j vm                                                                                                                                    |
    |   35 | retrieve the IP of a vm             | IP=`vca -j vm -a ubu | jq '.vms[0].IPs[0]'` && echo $IP                                                                                      |
    |   36 | list edge gateway NAT rules         | vca nat                                                                                                                                      |
    |   37 | add edge gateway DNAT rule          | vca nat add --type DNAT --original_ip 107.189.93.162 --original_port 22 --translated_ip 192.168.109.2 --translated_port 22 --protocol tcp    |
    |   38 | add edge gateway SNAT rule          | vca nat add --type SNAT --original_ip 192.168.109.0/24 --translated_ip 107.189.93.162                                                        |
    |   39 | add edge gateway rules from file    | vca nat add --file natrules.yaml                                                                                                             |
    |   40 | delete edge gateway NAT rule        | vca nat delete --type DNAT --original_ip 107.189.93.162 --original_port 22 --translated_ip 192.168.109.4 --translated_port 22 --protocol tcp |
    |   41 | delete all edge gateway NAT rules   | vca nat delete --all                                                                                                                         |
    |   42 | show the REST calls in the command  | vca --debug vm                                                                                                                               |
    |   43 | show version                        | vca --version                                                                                                                                |
    |   44 | show help                           | vca --help                                                                                                                                   |
    |   45 | show command help                   | vca <command> --help                                                                                                                         |
    

When using a file to indicate the edge gateway NAT rules, use the following YAML syntax:

    
    - NAT_rules:
    
        - type: SNAT
          original_ip: 192.168.109.0/24
          original_port: any
          translated_ip: 107.189.93.162
          translated_port: any
          protocol: any
          
        - type: DNAT
          original_ip: 107.189.93.162
          original_port: 22
          translated_ip: 192.168.109.2
          translated_port: 22
          protocol: tcp
          
        - type: DNAT
          original_ip: 107.189.93.162
          original_port: 80
          translated_ip: 192.168.109.2
          translated_port: 80
          protocol: tcp
          
        - type: DNAT
          original_ip: 107.189.93.162
          original_port: 322
          translated_ip: 192.168.109.3
          translated_port: 22
          protocol: tcp
          
        - type: DNAT
          original_ip: 107.189.93.162
          original_port: 422
          translated_ip: 192.168.109.4
          translated_port: 22
          protocol: tcp
    


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
        catalog   Operations with Catalogs
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
      

