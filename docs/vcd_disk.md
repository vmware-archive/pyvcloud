```
Usage: vcd disk [OPTIONS] COMMAND [ARGS]...

  Manage independent disks in vCloud Director.

      Examples
          vcd disk list
              Get list of independent disks in current virtual datacenter.
  
          vcd disk info disk1
              Get details of the disk named 'disk1'.
  
          vcd disk info disk1 --id 91b3a2e2-fd02-412b-9914-9974d60b2351
              Get details of the disk named 'disk1' that has the supplied id.
  
          vcd disk create disk1 100 --description '100 MB Disk'
              Create a new 100 MB independent disk named 'disk1' using the default storage profile.
  
          vcd disk delete disk1
              Delete an existing independent disk named 'disk1'.
  
          vcd disk update disk1 15
              Update an existing independent disk updating its size and storage profile.
      

Options:
  -h, --help  Show this message and exit.

Commands:
  create  create a disk
  delete  delete a disk
  info    show disk details
  list    list disks
  update  update disk

```
