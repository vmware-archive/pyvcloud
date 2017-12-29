```
Usage: vcd [OPTIONS] COMMAND [ARGS]...

  VMware vCloud Director Command Line Interface.

      Environment Variables
          VCD_USE_COLORED_OUTPUT
              If this environment variable is set, and it's value is not '0',
              the command vcd info will print the output in color. The effect
              of the environment variable will be overridden by the param
              --colorized/--no-colorized.
       

Options:
  -d, --debug                   Enable debug
  -j, --json                    Results as JSON object
  -n, --no-wait                 Don't wait for task
  --colorized / --no-colorized  print info in color or monochrome
  -h, --help                    Show this message and exit.

Commands:
  catalog  work with catalogs
  disk     manage independent disks
  help     show help
  info     show resource details
  login    login to vCD
  logout   logout from vCD
  netpool  work with network pools
  org      work with organizations
  profile  manage profiles
  pvdc     work with provider virtual datacenters
  pwd      current resources in use
  right    work with rights
  role     work with roles
  search   search resources
  system   manage system settings
  task     work with tasks
  user     work with users in current organization
  vapp     manage vApps
  vdc      work with virtual datacenters
  version  show version
  vm       manage VMs

```
