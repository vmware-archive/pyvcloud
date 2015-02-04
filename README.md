vca-cli
========

Command Line Interface for VMware vCloud Air.

> Release early, release often.

This project is under development.

Installation:

    
    $ pip install vca-cli
    

Upgrade from a previous installation:

        
    $ pip install vca-cli --upgrade
    

Install completions for oh-my-zsh

    
    $ ln -s ~/vca-cli/_vca ~/.oh-my-zsh/completions/_vca
    

Uses [pyvcloud](https://github.com/vmware/pyvcloud "Title"), Python SDK for VMware vCloud.

Usage:

Login

    
    # vCA on demand
    vca login user@domain.com --password ********
    # same as
    vca login user@domain.com --password ******** --host iam.vchs.vmware.com --type ondemand --version 5.7
    
    # vCA subscription
    vca login user@domain.com --password ******** --host vchs.vmware.com --type subscription --version 5.6
    
    # vCD
    vca login user@domain.com --password ******** --host vcdhost.domain.com --org myorg --type vcd --version 5.6
    


On Demand, login to a specific instance and get the details of the instance (organization):

    
    vca login user@domain.com --password ********
    vca instances
    vca login user@domain.com --password ******** --instance c40ba6b4-c158-49fb-b164-5c66f90344fa
    vca org
    

Connection status

    
    vca status
    
    profile:         default
    host:            https://iam.vchs.vmware.com
    service type:    ondemand
    service version: 5.7
    user:            user@domain.com
    session:         active
    

Logout

    
    vca logout
    

