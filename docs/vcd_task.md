```
Usage: vcd task [OPTIONS] COMMAND [ARGS]...

  Work with tasks in vCloud Director.

      Examples
          vcd task list running
              Get list of running tasks.
  
          vcd task info 4a115aa5-9657-4d97-a8c2-3faf43fb45dd
              Get details of task by id.
  
          vcd task wait 4a115aa5-9657-4d97-a8c2-3faf43fb45dd
              Wait until task is complete.
  
          vcd task update aborted 4a115aa5-9657-4d97-a8c2-3faf43fb45dd
              Abort task by id, requires login as 'system administrator'.
      

Options:
  -h, --help  Show this message and exit.

Commands:
  info    show task details
  list    list tasks
  update  update task status
  wait    wait until task is complete

```
