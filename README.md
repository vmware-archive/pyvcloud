vca-cli
========

Command Line Interface for VMware vCloud.

> Release early, release often.

This project is under development.

install completions for oh-my-zsh

> ln -s ~/vca-cli/_vca ~/.oh-my-zsh/completions/_vca

Usage:


    > vca --help
    Usage: vca [OPTIONS] COMMAND [ARGS]...
    
      A command line interface to VMware vCloud.
      
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
      
    %> vca login --help
    Usage: vca login [OPTIONS] USER
    
      Login to a vCloud service
      
    Options:
      -H, --host TEXT
      -p, --password TEXT
      -h, --help           Show this message and exit.
      
    
    > vca login pgomez@vmware.com
    Password: ********
    Login successful with profile 'default'
    

➜  vca-cli git:(master) ✗ vca --profile default profiles default
Usage: vca profiles [OPTIONS] [list | set | del | select]

Error: Invalid value for "operation": invalid choice: default. (choose from list, set, del, select)
➜  vca-cli git:(master) ✗ vca --profile default profiles select
Profile-default
host=https://vchs.vmware.com
user=pgomez@vmware.com
token=ae9f1dfbb4707285558bed84130bf05784e827a0,c2b79fe0-c0a7-4da6-8658-b6f00d2d910b%3BVMware+Sales+Demo%3B055dba95-ed61-4fe1-932c-d682d83f529c%3Bpgomez%40vmware.com%3B60c686e1-b1cf-4506-ab9c-2a69e89580b1%3B2%233%3B1417745406979%3Btrue%3Bfalse
service=85-719
gateway=AppServices
datacenter=AppServices
Profile-emc
host=https://vchs.vmware.com
user=vchs-cert2@vmware.com
token=0cd3ec00bf17b8e287654fd2c77d16b9d7011bae,8eaea9cc-1f64-4f55-a315-3a4322cc14ab%3Bvchs-cert2%3B74a06895-b01a-4c6c-9ad6-5f64b98f8bd2%3Bvchs-cert2%40vmware.com%3Bf76183c2-73e8-4109-b3cf-83289ef85d2f%3B1%3B1417725844645%3Btrue%3Bfalse
service=M755281541-1756
datacenter=M755281541-1756
gateway=M755281541-1756
Global
profile=default
Profile-vmop
host=https://vchs.vmware.com
user=pgomez@vmware.com
token=9104261adc036080bd255e6b029cfa61f23d11e7,c2b79fe0-c0a7-4da6-8658-b6f00d2d910b%3BVMware+Sales+Demo%3B055dba95-ed61-4fe1-932c-d682d83f529c%3Bpgomez%40vmware.com%3Bf559c02b-1bad-472b-9d22-696f5350ce0f%3B2%233%3B1418173611291%3Btrue%3Bfalse
service=M735816878-4430
datacenter=M735816878-4430
gateway=M735816878-4430
➜  vca-cli git:(master) ✗ vca login pgomez@vmware.com
Password:
Login successful with profile 'default'
➜  vca-cli git:(master) ✗ vca services
Available services for 'default' profile:
| ID              | Type                   | Region          |
|-----------------+------------------------+-----------------|
| 85-719          | compute:dedicatedcloud | US - Nevada     |
| 20-162          | compute:vpc            | US - Nevada     |
| M536557417-4609 | compute:dr2c           | US - California |
| M869414061-4607 | compute:dr2c           | US - Nevada     |
| M409710659-4610 | compute:dr2c           | US - Texas      |
| M371661272-4608 | compute:dr2c           | US - Virginia   |
➜  vca-cli git:(master) ✗ vca --service 85-719 datacenters
Usage: vca [OPTIONS] COMMAND [ARGS]...

Error: no such option: --service
➜  vca-cli git:(master) ✗ vca datacenters
Available datacenters in service '85-719' for 'default' profile:
| Virtual Data Center   | Status   | Service ID   | Service Type           | Region      |
|-----------------------+----------+--------------+------------------------+-------------|
| Gwyther               | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
| ODONOVAN              | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
| Villegas              | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
| CANTON                | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
| Schmerbeck            | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
| Momber                | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
| FedCloudHybrid        | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
| Stephenson            | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
| Denny                 | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
| Jenkins               | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
| Captain_Andy          | Error    | 85-719       | compute:dedicatedcloud | US - Nevada |
| Foley                 | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
| COWAN                 | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
| kaczmarek             | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
| Cohen                 | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
| Brady                 | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
| SBruno                | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
| AppServices           | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
➜  vca-cli git:(master) ✗ vca help
Usage: vca [OPTIONS] COMMAND [ARGS]...

Error: No such command "help".
➜  vca-cli git:(master) ✗ vca --help
Usage: vca [OPTIONS] COMMAND [ARGS]...

  A command line interface to VMware vCloud.

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
➜  vca-cli git:(master) ✗ vca login pgomez@vmware.com
Password:
Login successful with profile 'default'
➜  vca-cli git:(master) ✗ vca services
Available services for 'default' profile:
| ID              | Type                   | Region          |
|-----------------+------------------------+-----------------|
| 85-719          | compute:dedicatedcloud | US - Nevada     |
| 20-162          | compute:vpc            | US - Nevada     |
| M536557417-4609 | compute:dr2c           | US - California |
| M869414061-4607 | compute:dr2c           | US - Nevada     |
| M409710659-4610 | compute:dr2c           | US - Texas      |
| M371661272-4608 | compute:dr2c           | US - Virginia   |
➜  vca-cli git:(master) ✗ vca datacenters --service 85-719
Available datacenters in service '85-719' for 'default' profile:
| Virtual Data Center   | Status   | Service ID   | Service Type           | Region      |
|-----------------------+----------+--------------+------------------------+-------------|
| Gwyther               | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
| ODONOVAN              | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
| Villegas              | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
| CANTON                | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
| Schmerbeck            | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
| Momber                | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
| FedCloudHybrid        | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
| Stephenson            | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
| Denny                 | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
| Jenkins               | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
| Captain_Andy          | Error    | 85-719       | compute:dedicatedcloud | US - Nevada |
| Foley                 | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
| COWAN                 | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
| kaczmarek             | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
| Cohen                 | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
| Brady                 | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
| SBruno                | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
| AppServices           | Active   | 85-719       | compute:dedicatedcloud | US - Nevada |
➜  vca-cli git:(master) ✗ vca vapps --service 85-719 --datacenter AppServices
list of vApps
| Service   | Datacenter   | vApp   | Status     | Owner             | Date Created        |
|-----------+--------------+--------+------------+-------------------+---------------------|
| 85-719    | 85-719       | ub     | Powered on | pgomez@vmware.com | 12/11/2014 05:41:17 |
| 85-719    | 85-719       | cts    | Powered on | pgomez@vmware.com | 12/11/2014 02:58:13 |
➜  vca-cli git:(master) ✗ vca gateways --service 85-719 --datacenter AppServices
Available gateways in datacenter 'AppServices' in service '85-719' for 'default' profile:
| Datacenter   | Gateway     |
|--------------+-------------|
| AppServices  | AppServices |
➜  vca-cli git:(master) ✗ vca profiles --service 85-719 --datacenter AppServices --gateway AppsServices set
Profile-default
host=https://vchs.vmware.com
user=pgomez@vmware.com
token=4e5aac22e2af84e80b0d01017d25e3df9a6b29b4,c2b79fe0-c0a7-4da6-8658-b6f00d2d910b%3BVMware+Sales+Demo%3B055dba95-ed61-4fe1-932c-d682d83f529c%3Bpgomez%40vmware.com%3B5dc4b347-012a-4912-bf74-f5be8f5a5925%3B2%233%3B1418173708510%3Btrue%3Bfalse
service=85-719
gateway=AppsServices
datacenter=AppServices
Profile-emc
host=https://vchs.vmware.com
user=vchs-cert2@vmware.com
token=0cd3ec00bf17b8e287654fd2c77d16b9d7011bae,8eaea9cc-1f64-4f55-a315-3a4322cc14ab%3Bvchs-cert2%3B74a06895-b01a-4c6c-9ad6-5f64b98f8bd2%3Bvchs-cert2%40vmware.com%3Bf76183c2-73e8-4109-b3cf-83289ef85d2f%3B1%3B1417725844645%3Btrue%3Bfalse
service=M755281541-1756
datacenter=M755281541-1756
gateway=M755281541-1756
Global
profile=default
Profile-vmop
host=https://vchs.vmware.com
user=pgomez@vmware.com
token=9104261adc036080bd255e6b029cfa61f23d11e7,c2b79fe0-c0a7-4da6-8658-b6f00d2d910b%3BVMware+Sales+Demo%3B055dba95-ed61-4fe1-932c-d682d83f529c%3Bpgomez%40vmware.com%3Bf559c02b-1bad-472b-9d22-696f5350ce0f%3B2%233%3B1418173611291%3Btrue%3Bfalse
service=M735816878-4430
datacenter=M735816878-4430
gateway=M735816878-4430
➜  vca-cli git:(master) ✗ vca vapps
list of vApps
| Service   | Datacenter   | vApp   | Status     | Owner             | Date Created        |
|-----------+--------------+--------+------------+-------------------+---------------------|
| 85-719    | 85-719       | ub     | Powered on | pgomez@vmware.com | 12/11/2014 05:41:17 |
| 85-719    | 85-719       | cts    | Powered on | pgomez@vmware.com | 12/11/2014 02:58:13 |
➜  vca-cli git:(master) ✗ vca nat
list of dnat rules
Gateway not found
➜  vca-cli git:(master) ✗ vca profiles --service 85-719 --datacenter AppServices --gateway AppServices set
Profile-default
host=https://vchs.vmware.com
user=pgomez@vmware.com
token=4e5aac22e2af84e80b0d01017d25e3df9a6b29b4,c2b79fe0-c0a7-4da6-8658-b6f00d2d910b%3BVMware+Sales+Demo%3B055dba95-ed61-4fe1-932c-d682d83f529c%3Bpgomez%40vmware.com%3B5dc4b347-012a-4912-bf74-f5be8f5a5925%3B2%233%3B1418173708510%3Btrue%3Bfalse
service=85-719
gateway=AppServices
datacenter=AppServices
Profile-emc
host=https://vchs.vmware.com
user=vchs-cert2@vmware.com
token=0cd3ec00bf17b8e287654fd2c77d16b9d7011bae,8eaea9cc-1f64-4f55-a315-3a4322cc14ab%3Bvchs-cert2%3B74a06895-b01a-4c6c-9ad6-5f64b98f8bd2%3Bvchs-cert2%40vmware.com%3Bf76183c2-73e8-4109-b3cf-83289ef85d2f%3B1%3B1417725844645%3Btrue%3Bfalse
service=M755281541-1756
datacenter=M755281541-1756
gateway=M755281541-1756
Global
profile=default
Profile-vmop
host=https://vchs.vmware.com
user=pgomez@vmware.com
token=9104261adc036080bd255e6b029cfa61f23d11e7,c2b79fe0-c0a7-4da6-8658-b6f00d2d910b%3BVMware+Sales+Demo%3B055dba95-ed61-4fe1-932c-d682d83f529c%3Bpgomez%40vmware.com%3Bf559c02b-1bad-472b-9d22-696f5350ce0f%3B2%233%3B1418173611291%3Btrue%3Bfalse
service=M735816878-4430
datacenter=M735816878-4430
gateway=M735816878-4430
➜  vca-cli git:(master) ✗ vca nat
list of dnat rules
|   Rule ID | Enabled   | Type   | Original IP      | Original Port   | Translated IP   | Translated Port   | Protocol   | Applied On   |
|-----------+-----------+--------+------------------+-----------------+-----------------+-------------------+------------+--------------|
|     65538 | True      | SNAT   | 192.168.109.0/24 | any             | 192.240.158.81  | any               | any        | d0p1-ext     |
|     65537 | True      | DNAT   | 192.240.158.81   | 22              | 192.168.109.2   | 22                | tcp        | d0p1-ext     |
|     65539 | True      | DNAT   | 192.240.158.81   | 80              | 192.168.109.2   | 80                | tcp        | d0p1-ext     |
|     65540 | True      | DNAT   | 192.240.158.81   | 8080            | 192.168.109.4   | 8080              | tcp        | d0p1-ext     |
|     65541 | True      | DNAT   | 192.240.158.81   | 23              | 192.168.109.2   | 22                | tcp        | d0p1-ext     |
➜  vca-cli git:(master) ✗
