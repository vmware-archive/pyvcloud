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
              Create a new vApp.
  
          vcd vapp create my-catalog my-template my-vapp \
                   --cpu 4 --memory 4096 --network net1
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
      

Options:
  -h, --help  Show this message and exit.

Commands:
  create        create a vApp
  delete        delete a vApp
  info          show vApp details
  list          list vApps
  update-lease  update vApp lease

```
