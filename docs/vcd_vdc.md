```
Usage: vcd vdc [OPTIONS] COMMAND [ARGS]...

  Work with virtual datacenters in vCloud Director.

      Examples
          vcd vdc list
              Get list of virtual datacenters in current organization.
  
          vcd vdc info my-vdc
              Get details of the virtual datacenter 'my-vdc'.
  
          vcd vdc use my-vdc
              Set virtual datacenter 'my-vdc' as default.
  
          vcd vdc create dev-vdc -p prov-vdc -n net-pool -s '*' \
              -a ReservationPool -d 'vDC for development'
              Create new virtual datacenter.
  
          vcd vdc disable dev-vdc
              Disable virtual datacenter.
  
          vcd vdc enable dev-vdc
              Enable virtual datacenter.
  
          vcd vdc delete -y dev-vdc
              Delete virtual datacenter.
      

Options:
  -h, --help  Show this message and exit.

Commands:
  create   create a virtual datacenter
  delete   delete a virtual datacenter
  disable  disable a virtual datacenter
  enable   enable a virtual datacenter
  info     show virtual datacenter details
  list     list of virtual datacenters
  use      set active virtual datacenter

```
