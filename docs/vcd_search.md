```
Usage: vcd search [OPTIONS] [resource-type]

  Search for resources in vCloud Director.

      Description
          Search for resources of the provided type. Resource type is not case
          sensitive. When invoked without a resource type, list the available
          types to search for. Admin types are only allowed when the user is
          the system administrator.
  
          Filters can be applied to the search.
  
      Examples
          vcd search
              lists available resource types.
  
          vcd search task
              Search for all tasks in current organization.
  
          vcd search task --filter 'status==running'
              Search for running tasks in current organization.
  
          vcd search admintask --filter 'status==running'
              Search for running tasks in all organizations,
              system administrator only.
  
          vcd search task --filter 'id==ffb96443-d7f3-4200-825d-0f297388ebc0'
              Search for a task by id
  
          vcd search vapp
              Search for vApps.
  
          vcd search vapp -f 'metadata:cse.node.type==STRING:master'
              Search for vApps by metadata.
  
          vcd search vapp -f \
          'metadata:vapp.origin.name==STRING:photon-custom-hw11-2.0-304b817.ova'
              Search for vApps instantiated from template
  
          vcd search vapp -f \
          'numberOfCpus=gt=4;memoryAllocationMB=gt=10000;storageKB=gt=10000000'
              Search for resource intensive vApps
  
          vcd search vm
              Search for virtual machines.
      

Options:
  -f, --filter [query-filter]  query filter
  -h, --help                   Show this message and exit.

```
