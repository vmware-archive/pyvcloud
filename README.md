vca-cli
========

Command Line Interface for VMware vCloud Air.

> Release early, release often.

This project is under development.

Installation:

    
    pip install vca-cli
    

Install completions for oh-my-zsh

> ln -s ~/vca-cli/_vca ~/.oh-my-zsh/completions/_vca

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
      
    > vca login --help
    Usage: vca login [OPTIONS] USER
    
      Login to a vCloud service
      
    Options:
      -H, --host TEXT
      -p, --password TEXT
      -h, --help           Show this message and exit.
      
    
    > vca login myname@mycompany.com
    Password: ********
    Login successful with profile 'default'
    
    
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
    


