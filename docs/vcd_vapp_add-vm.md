```
Usage: vcd vapp add-vm [OPTIONS] <target-vapp> <source-vapp> <source-vm>

Options:
  -c, --catalog name             Name of the catalog if the source vApp is a
                                 template
  -t, --target-vm name           Rename the target VM with this name
  -o, --hostname hostname        Customize VM and set hostname in the guest OS
  -n, --network name             vApp network to connect to
  -i, --ip-allocation-mode mode  IP allocation mode
  -s, --storage-profile name     Name of the storage profile for the VM
  --password-auto                Autogenerate administrator password
  --accept-all-eulas             Accept all EULAs
  -h, --help                     Show this message and exit.

```
