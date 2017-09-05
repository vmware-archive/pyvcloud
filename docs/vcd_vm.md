```
Usage: vcd vm [OPTIONS] COMMAND [ARGS]...

  Manage VMs in vCloud Director.

      Examples
          vcd vm list
              Get list of VMs in current virtual datacenter.
  
          vcd vm run myvapp myvm vcs.server.com 'administrator@vsphere.local' \
              'pa$$w0rd' root 'pa$$w0rd' /usr/bin/date '>/tmp/now.txt'
              Run command on guest OS, requires access to vCenter.
  
          vcd vm upload myvapp myvm vcs.server.com 'administrator@vsphere.local' \
              'pa$$w0rd' root 'pa$$w0rd' ./my-commands.sh /tmp/my-commands.sh
              Upload file to guest OS, requires access to vCenter.
  
          vcd vm download myvapp myvm vcs.server.com 'administrator@vsphere.local' \
              'pa$$w0rd' root 'pa$$w0rd' /etc/hosts
              Download file from guest OS, requires access to vCenter.
  
          vcd vm download myvapp myvm vcs.server.com 'administrator@vsphere.local' \
              'pa$$w0rd' root 'pa$$w0rd' /etc/hosts ./hosts.txt
              Download file from guest OS and save locally, requires access to vCenter.
      

Options:
  -h, --help  Show this message and exit.

Commands:
  download  download file from guest
  info      show VM details
  list      list VMs
  run       run command in guest
  upload    upload file to guest

```
