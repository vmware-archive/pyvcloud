```
Usage: vcd role [OPTIONS] COMMAND [ARGS]...

  Work with roles and rights

      Examples
          vcd role list
              Get list of roles in the current organization.
  
          vcd role list_rights myRole
              Get list of rights associated with a given role.
  
          vcd role create myRole myDescription 'Disk: View Properties' \
              'Provider vDC: Edit' --org myOrg
              Create a role with zero or more rights in the specified
              Organization (defaults to current Organization in use)
      

Options:
  -h, --help  Show this message and exit.

Commands:
  create       Creates role in the specified Organization (defaults to the
               current Organization in use)
  list         list roles
  list-rights  list rights of a role

```
