```
Usage: vcd role [OPTIONS] COMMAND [ARGS]...

  Work with roles.      Description        All sub-commands execute in the
  context of specified organization;        it defaults to current
  organization-in-use if --org option is not specified.

      Examples
          vcd role list
              Get list of roles in the current organization.
  
          vcd role list-rights myRole
              Get list of rights associated with a given role.
  
          vcd role create myRole myDescription 'Disk: View Properties' \
              'Provider vDC: Edit' --org myOrg
              Creates a role with zero or more rights.
  
          vcd role delete myRole -o myOrg
              Deletes a role from the organization.
  
          vcd role link myRole -o myOrg
              Links the role to it's original template.
  
          vcd role unlink myRole -o myOrg
              Unlinks the role from its template.
      

Options:
  -h, --help  Show this message and exit.

Commands:
  create       Creates role in the specified Organization (defaults to the
               current Organization in use)
  delete       Deletes role in the specified Organization(defaults to the
               current organization in use
  link         Link the role of a given org to its template
  list         list roles
  list-rights  list rights of a role
  unlink       Unlink the role of a given org from its template

```
