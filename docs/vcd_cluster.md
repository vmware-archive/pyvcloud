```
Usage: vcd cluster [OPTIONS] COMMAND [ARGS]...

  Work with kubernetes clusters in vCloud Director.

      Examples
          vcd cluster list
              Get list of kubernetes clusters in current virtual datacenter.
  
          vcd cluster create dev-cluster
              Create a kubernetes cluster in current virtual datacenter.
  
          vcd cluster create prod-cluster --nodes 4
              Create a kubernetes cluster with 4 worker nodes.
  
          vcd cluster delete dev-cluster
              Deletes a kubernetes cluster by name.
      

Options:
  -h, --help  Show this message and exit.

Commands:
  config  get cluster config
  create  create cluster
  delete  delete cluster
  list    list clusters

```
