`vcd-cli` can be extended with custom or third party commands.

To install a new command:

1. install the python package that implements the new command
2. add full path of the module that implements the new command to the `extensions` element in the profiles (file `~/.vcd-cli/profiles.yaml`)


As an example, to add [CSE](https://vmware.github.io/container-service-extension/) commands to your local `vcd-cli` installation:

Install CSE package with:

```shell
$ pip install container-service-extension --pre --upgrade
```

Edit `~/.vcd-cli/profiles.yaml` and add the following two lines between the `active` and `profiles` entries:

`~/.vcd-cli/profiles.yaml` before changes:
```yaml
active: default
profiles:
```

after changes:
```yaml
active: default
extensions:
- container_service_extension.client.cse
profiles:
```

Validate the new commands are installed with:
```shell
$ vcd cse
Usage: vcd cse [OPTIONS] COMMAND [ARGS]...

  Work with kubernetes clusters in vCloud Director.

    Examples
        vcd cse cluster list
            Get list of kubernetes clusters in current virtual datacenter.
        ...
```
