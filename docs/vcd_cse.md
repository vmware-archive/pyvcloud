```
Usage: vcd cse [OPTIONS] COMMAND [ARGS]...

  Work with kubernetes clusters in vCloud Director.

      Description
          The cse command works with kubernetes clusters on vCloud Director.
  
          'vcd cse cluster create' creates a new kubernetes cluster in the
          current virtual datacenter.
  
          Cluster names should follow the syntax for valid hostnames and can have
          up to 25 characters .`system`, `template` and `swagger*` are reserved words and
          cannot be used to name a cluster.

      Examples
          vcd cse cluster list
              Get list of kubernetes clusters in current virtual datacenter.
  
          vcd cse cluster create dev-cluster --network net1
              Create a kubernetes cluster in current virtual datacenter.
  
          vcd cse cluster create prod-cluster --nodes 4 \
                      --network net1 --storage-profile '*'
              Create a kubernetes cluster with 4 worker nodes.
  
          vcd cse cluster delete dev-cluster
              Delete a kubernetes cluster by name.
  
          vcd cse cluster create c1 --nodes 0 --network net1
              Create a single node kubernetes cluster for dev/test.
  
          vcd cse node list c1
              List nodes in a cluster.
  
          vcd cse template list
              Get list of CSE templates available.
  
          vcd cse version
              Display version.
      

Options:
  -h, --help  Show this message and exit.

Commands:
  cluster   work with clusters
  node      work with nodes
  system    work with CSE service
  template  work with templates
  version   show version

```
