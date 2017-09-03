```
Usage: vcd cluster [OPTIONS] COMMAND [ARGS]...

  Work with kubernetes clusters in vCloud Director.

      Examples
          vcd cluster list
              Get list of kubernetes clusters in current virtual datacenter.
  
          vcd cluster create k8s-cluster --nodes 2
              Create a kubernetes cluster in current virtual datacenter.
  
          vcd cluster delete 692a7b81-bb75-44cf-9070-523a4b304733
              Deletes a kubernetes cluster by id.


Options:
  -h, --help  Show this message and exit.

Commands:
  config  get cluster config
  create  create cluster
  delete  delete cluster
  list    list clusters
```
