```
Usage: vcd cse cluster create [OPTIONS] NAME

Options:
  -N, --nodes INTEGER         Number of nodes to create
  -c, --cpu INTEGER           Number of virtual CPUs on each node
  -m, --memory INTEGER        Amount of memory (in MB) on each node
  -n, --network TEXT          Network name  [required]
  -s, --storage-profile TEXT  Name of the storage profile for the nodes
  -k, --ssh-key FILENAME      SSH public key to connect to the guest OS on the
                              VM
  -t, --template TEXT         Name of the template to instantiate nodes from
  -h, --help                  Show this message and exit.

```
