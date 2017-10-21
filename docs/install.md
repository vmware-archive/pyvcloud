CentOS 7

```shell
$ cat /etc/redhat-release
  CentOS Linux release 7.4.1708 (Core)

$ sudo yum install epel-release
$ sudo yum install python34 python34-devel -y
$ sudo yum install python34-setuptools -y
$ sudo easy_install-3.4 pip

$ pip3 install --user --pre vcd-cli

$ vcd –j version

{
    "description": "VMware vCloud Director Command Line Interface",
    "product": "vcd-cli",
    "python": "3.4.2",
    "version": "19.2.1"
}
```
