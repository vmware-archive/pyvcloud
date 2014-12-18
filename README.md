vca-cli
========

Command Line Interface for VMware vCloud Air.

> Release early, release often.

This project is under development.

Installation:

    
    pip install vca-cli
    

Install completions for oh-my-zsh

    
    ln -s ~/vca-cli/_vca ~/.oh-my-zsh/completions/_vca
    

Uses [pyvcloud](https://github.com/vmware/pyvcloud "Title"), Python SDK for VMware vCloud.

Usage:

    
    > vca --help
    Usage: vca [OPTIONS] COMMAND [ARGS]...
    
      VMware vCloud Air Command Line Interface.
      
    Options:
      -p, --profile <profile>  Profile id
      -v, --version            Show version
      -d, --debug              Enable debug
      -h, --help               Show this message and exit.
      
    Commands:
      catalogs     Operations with catalogs
      datacenters  Operations with virtual data centers
      disks        Operations with disks
      gateways     Operations with gateways
      login        Login to a vCloud service
      logout       Logout from a vCloud service
      nat          Operations with gateway NAT rules
      networks     Operations with networks
      profiles     Configure profiles
      services     Operations with services
      status       Show current status
      tasks        Operations with tasks
      templates    Operations with templates
      vapps        Operations with vApps
      vms          Operations with VMs  
      
      

Log in to vCloud Air:

      
    > vca login --help
    Usage: vca login [OPTIONS] USER
    
      Login to a vCloud service
      
    Options:
      -H, --host TEXT
      -p, --password TEXT
      -h, --help           Show this message and exit.
      
    
    > vca login myname@mycomp.com
    Password: ********
    Login successful with profile 'default'
    

Alternatively:

    
    > vca login myname@mycomp.com --password my_secret_password
    Login successful with profile 'default'
    

List services and virtual datacenters available to the user:

    
    > vca services    
    Available services for 'default' profile:
    | ID              | Type                   | Region          |
    |-----------------+------------------------+-----------------|
    | 85-719          | compute:dedicatedcloud | US - Nevada     |
    | 20-162          | compute:vpc            | US - Nevada     |
    | M536557417-4609 | compute:dr2c           | US - California |
    | M869414061-4607 | compute:dr2c           | US - Nevada     |
    | M409710659-4610 | compute:dr2c           | US - Texas      |
    | M371661272-4608 | compute:dr2c           | US - Virginia   |    
    
    
    > vca datacenters --service 85-719
    Available datacenters in service '85-719' for 'default' profile:
    | Virtual Data Center   | Status   | Service ID   | Service Type           | Region      |
    |-----------------------+----------+--------------+------------------------+-------------|
    | Marketing             | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
    | RnD                   | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
    | Production            | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
    | DevOps                | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
    | AppServices           | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |    
    
    
    > vca gateways --service 85-719 --datacenter AppServices
    Available gateways in datacenter 'AppServices' in service '85-719' for 'default' profile:
    | Datacenter   | Gateway     |
    |--------------+-------------|
    | AppServices  | AppServices |
    
    

Configure values for service, datacenter and gateway and set as the default profile:

    
    > vca profiles --service 85-719 --datacenter AppServices --gateway AppServices set
    Profile-default
    	host=https://vchs.vmware.com
    	user=myname@mycomp.com
    	service=85-719
    	gateway=AppServices
    	datacenter=AppServices
    	token=d188143a5d4642745d9c46c696...
    
    
    > vca status
    profile:    default
    host:       https://vchs.vmware.com
    user:       myname@mycomp.com
    service:    85-719
    datacenter: AppServices
    gateway:    AppServices
    session:    active    
    

List vApps, VMs and templates:

    
    
    > vca vapps --vms
    list of vApps
    | Service   | Datacenter   | vApp   | VMs     | Status     | Owner            | Date Created        |
    |-----------+--------------+--------+---------+------------+------------------+---------------------|
    | 85-719    | AppServices  | ub     | ['ub']  | Powered on | myname@mycom.com | 12/11/2014 05:41:17 |
    | 85-719    | AppServices  | cts    | ['cts'] | Powered on | myname@mycom.com | 12/11/2014 02:58:13 |    
    
    
    > vca templates
    list of templates
    | Catalog        | Template                                 | Status   | Owner             |   # VMs |   # CPU |   Memory(GB) |   Storage(GB) | Storage Profile   |
    |----------------+------------------------------------------+----------+-------------------+---------+---------+--------------+---------------+-------------------|
    | blueprints     | cts_6_4_64bit                            | RESOLVED | myname@mycomp.com |       1 |       1 |            2 |            20 | SSD-Accelerated   |
    | Public Catalog | W2K8-STD-R2-64BIT-SQL2K8-STD-R2-SP2      | RESOLVED | catalog_admin     |       1 |       1 |            4 |            41 | SSD-Accelerated   |
    | Public Catalog | W2K12-STD-64BIT-SQL2K12-STD-SP1          | RESOLVED | catalog_admin     |       1 |       1 |            4 |            41 | SSD-Accelerated   |
    | Public Catalog | CentOS64-32Bit                           | RESOLVED | system            |       1 |       1 |            1 |            20 | SSD-Accelerated   |
    | Public Catalog | W2K12-STD-64BIT-SQL2K12-WEB-SP1          | RESOLVED | catalog_admin     |       1 |       1 |            4 |            41 | SSD-Accelerated   |
    | Public Catalog | W2K12-STD-R2-64BIT                       | RESOLVED | system            |       1 |       1 |            4 |            41 | SSD-Accelerated   |
    | Public Catalog | W2K12-STD-R2-SQL2K14-WEB                 | RESOLVED | system            |       1 |       1 |            4 |            41 | SSD-Accelerated   |
    | Public Catalog | CentOS64-64Bit                           | RESOLVED | system            |       1 |       1 |            1 |            20 | SSD-Accelerated   |
    | Public Catalog | W2K8-STD-R2-64BIT-SQL2K8-WEB-R2-SP2      | RESOLVED | catalog_admin     |       1 |       1 |            4 |            41 | SSD-Accelerated   |
    | Public Catalog | Ubuntu Server 12.04 LTS (i386 20140927)  | RESOLVED | system            |       1 |       1 |            1 |            10 | SSD-Accelerated   |
    | Public Catalog | Ubuntu Server 12.04 LTS (amd64 20140927) | RESOLVED | system            |       1 |       1 |            1 |            10 | SSD-Accelerated   |
    | Public Catalog | CentOS63-64Bit                           | RESOLVED | system            |       1 |       1 |            1 |            20 | SSD-Accelerated   |
    | Public Catalog | W2K8-STD-R2-64BIT                        | RESOLVED | system            |       1 |       1 |            2 |            41 | SSD-Accelerated   |
    | blueprints     | ubuntu_1204_64bit                        | RESOLVED | myname@mycomp.com |       1 |       2 |            4 |            67 | SSD-Accelerated   |
    | Public Catalog | W2K12-STD-64BIT                          | RESOLVED | catalog_admin     |       1 |       1 |            4 |            41 | SSD-Accelerated   |
    | Public Catalog | CentOS63-32Bit                           | RESOLVED | system            |       1 |       1 |            1 |            20 | SSD-Accelerated   |
    | Public Catalog | W2K12-STD-R2-SQL2K14-STD                 | RESOLVED | system            |       1 |       1 |            4 |            41 | SSD-Accelerated   |    
    
    

Working with Edge Gateway NAT rules:

    > vca nat
    list of nat rules
    |   Rule ID | Enabled   | Type   | Original IP      | Original Port   | Translated IP   | Translated Port   | Protocol   | Applied On   |
    |-----------+-----------+--------+------------------+-----------------+-----------------+-------------------+------------+--------------|
    |     65538 | True      | SNAT   | 192.168.109.0/24 | any             | 192.240.158.81  | any               | any        | d0p1-ext     |
    |     65537 | True      | DNAT   | 192.240.158.81   | 22              | 192.168.109.2   | 22                | tcp        | d0p1-ext     |
    |     65540 | True      | DNAT   | 192.240.158.81   | 8080            | 192.168.109.4   | 8080              | tcp        | d0p1-ext     |
    
    
    >vca nat add DNAT 192.240.158.81 80 192.168.109.2 80 tcp
    adding nat rule
    +-------------+-----------------------------------------------------------------------------------------------+
    | @startTime  | 2014-12-18T02:58:24.777Z                                                                      |
    +-------------+-----------------------------------------------------------------------------------------------+
    | @status     | running                                                                                       |
    +-------------+-----------------------------------------------------------------------------------------------+
    | @href       | https://p1v21-vcd.vchs.vmware.com/api/task/1e449f40-c25f-4037-8475-ff783dca5eef               |
    +-------------+-----------------------------------------------------------------------------------------------+
    | task:cancel | https://p1v21-vcd.vchs.vmware.com/api/task/1e449f40-c25f-4037-8475-ff783dca5eef/action/cancel |
    +-------------+-----------------------------------------------------------------------------------------------+
    |   Rule ID | Enabled   | Type   | Original IP      | Original Port   | Translated IP   | Translated Port   | Protocol   | Applied On   |
    |-----------+-----------+--------+------------------+-----------------+-----------------+-------------------+------------+--------------|
    |     65538 | True      | SNAT   | 192.168.109.0/24 | any             | 192.240.158.81  | any               | any        | d0p1-ext     |
    |     65537 | True      | DNAT   | 192.240.158.81   | 22              | 192.168.109.2   | 22                | tcp        | d0p1-ext     |
    |     65540 | True      | DNAT   | 192.240.158.81   | 8080            | 192.168.109.4   | 8080              | tcp        | d0p1-ext     |
    |     65541 | True      | DNAT   | 192.240.158.81   | 23              | 192.168.109.2   | 22                | tcp        | d0p1-ext     |
    |     65542 | True      | DNAT   | 192.240.158.81   | 80              | 192.168.109.2   | 80                | tcp        | d0p1-ext     |
    
    
    > vca nat del DNAT 192.240.158.81 80 192.168.109.2 80 tcp
    deleting nat rule
    +-------------+-----------------------------------------------------------------------------------------------+
    | @startTime  | 2014-12-18T02:56:55.677Z                                                                      |
    +-------------+-----------------------------------------------------------------------------------------------+
    | @status     | running                                                                                       |
    +-------------+-----------------------------------------------------------------------------------------------+
    | @href       | https://p1v21-vcd.vchs.vmware.com/api/task/fe423f3b-3d8d-4fff-ba0a-491f052723db               |
    +-------------+-----------------------------------------------------------------------------------------------+
    | task:cancel | https://p1v21-vcd.vchs.vmware.com/api/task/fe423f3b-3d8d-4fff-ba0a-491f052723db/action/cancel |
    +-------------+-----------------------------------------------------------------------------------------------+
    |   Rule ID | Enabled   | Type   | Original IP      | Original Port   | Translated IP   | Translated Port   | Protocol   | Applied On   |
    |-----------+-----------+--------+------------------+-----------------+-----------------+-------------------+------------+--------------|
    |     65538 | True      | SNAT   | 192.168.109.0/24 | any             | 192.240.158.81  | any               | any        | d0p1-ext     |
    |     65537 | True      | DNAT   | 192.240.158.81   | 22              | 192.168.109.2   | 22                | tcp        | d0p1-ext     |
    |     65540 | True      | DNAT   | 192.240.158.81   | 8080            | 192.168.109.4   | 8080              | tcp        | d0p1-ext     |
    |     65541 | True      | DNAT   | 192.240.158.81   | 23              | 192.168.109.2   | 22                | tcp        | d0p1-ext     |
    


