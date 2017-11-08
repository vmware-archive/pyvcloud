```
Usage: vcd vapp [OPTIONS] COMMAND [ARGS]...

  Manage vApps in vCloud Director.

      Examples
          vcd vapp list
              Get list of vApps in current virtual datacenter.
  
          vcd vapp info my-vapp
              Get details of the vApp 'my-vapp'.
  
          vcd vapp create my-catalog my-template my-vapp
              Create a new vApp with default settings.
  
          vcd vapp create my-catalog my-template my-vapp \
                   --cpu 4 --memory 4096 --network net1  \
                   --ip-allocation-mode pool
              Create a new vApp with customized settings.
  
          vcd vapp delete my-vapp --yes --force
              Delete a vApp.
  
          vcd --no-wait vapp delete my-vapp --yes --force
              Delete a vApp without waiting for completion.
  
          vcd vapp update-lease my-vapp 7776000
              Set vApp lease to 90 days.
  
          vcd vapp update-lease my-vapp 0
              Set vApp lease to no expiration.
  
          vcd vapp shutdown my-vapp --yes
              Gracefully shutdown a vApp.
  
          vcd vapp power-off my-vapp
              Power off a vApp.
  
          vcd vapp power-on my-vapp
              Power on a vApp.
  
          vcd vapp capture my-vapp my-catalog
              Capture a vApp as a template in a catalog.
      

Options:
  -h, --help  Show this message and exit.

Commands:
  capture       save a vApp as a template
  create        create a vApp
  delete        delete a vApp
  info          show vApp details
  list          list vApps
  power-off     power off a vApp
  power-on      power on a vApp
  shutdown      shutdown a vApp
  update-lease  update vApp lease

```
