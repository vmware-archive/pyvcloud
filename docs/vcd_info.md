```
Usage: vcd info [OPTIONS] [resource-type] [resource-id]

  Display details of a resource in vCloud Director.

      Description
          Display details of a resource with the provided type and id.
          Resource type is not case sensitive. When invoked without a resource
          type, list the available types. Admin resources are only allowed when
          the user is the system administrator.
  
      Examples
          vcd info task ffb96443-d7f3-4200-825d-0f297388ebc0
              Get details of task by id.
  
          vcd info vapp c48a4e1a-7bd9-4177-9c67-4c330016b99f
              Get details of vApp by id.
  
          vcd catalog list my-catalog                                 # list items
          vcd catalog info my-catalog my-item                         # get catalog item id
           vcd info catalogitem f653b137-0d14-4ea9-8f14-dcd2b7914110  # get vapp template id
           vcd info vapptemplate 53b83b27-1f2b-488e-9020-a27aee8cb640 # details of template
  
      See Also
          Several 'vcd' commands provide the id of a resource, including the
          'vcd search' command.
      

Options:
  -h, --help  Show this message and exit.

```
