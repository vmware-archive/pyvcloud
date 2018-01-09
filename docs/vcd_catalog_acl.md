```
Usage: vcd catalog acl [OPTIONS] COMMAND [ARGS]...

  Work with catalogs access control list in the current Organization.

      Examples
          vcd catalog acl add my-catalog 'org:TestOrg1:Change'  \
              'user:TestUser1:FullControl' 'org:TestOrg2'
              Add one or more access setting to the specified catalog.
              access-list is specified in the format
              '<subject-type>:<subject-name>:<access-level>'
              subject-type is one of 'org' ,'user'
              subject-name is either username or org name
              access-level is one of 'ReadOnly', 'Change', 'FullControl'
              'ReadOnly' by default. eg. 'org:TestOrg2'
  
          vcd catalog acl remove my-catalog 'org:TestOrg1' 'user:TestUser1'
              Remove one or more acl from the specified catalog. access-list is
              specified in the format '<subject-type>:<subject-name>'
              subject-type is one of 'org' ,'user'
              subject-name is either username or org name
  
          vcd catalog acl share my-catalog --access-level ReadOnly
              Share catalog access to all members of the current organization
  
          vcd catalog acl unshare my-catalog
              Unshare  catalog access from  all members of the current
              organization
  
          vcd catalog acl list my-catalog
              List acl of a catalog

          vcd catalog acl info my-catalog
              Get details of catalog access control settings



Options:
  -h, --help  Show this message and exit.

Commands:
  add      add access settings to a particular catalog
  list     list catalog access control list
  remove   remove access settings from a particular catalog
  share    share catalog access to all members of the currentorganization
  unshare  unshare catalog access from members of the current organization

```
