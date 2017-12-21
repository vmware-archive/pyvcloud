```
Usage: vcd org [OPTIONS] COMMAND [ARGS]...

  Work with organizations in vCloud Director.

      Examples
          vcd org list
              Get list of organizations.
  
          vcd org info my-org
              Get details of the organization 'my-org'.
  
          vcd org use my-org
              Set organization 'my-org' as default.
  
          vcd org create my-org-name my-org-fullname
              Create organization with 'my-org-name' and 'my-org-fullname'
  
          vcd org delete my-org-name
              Delete organization 'my-org-name'
  
          vcd org update my-org-name --enable
              Update organization 'my-org-name', e.g. enable the organization
      

Options:
  -h, --help  Show this message and exit.

Commands:
  create  create an organization
  delete  delete an organization
  info    show org details
  list    list organizations
  update  update an organization
  use     set active organization

```
