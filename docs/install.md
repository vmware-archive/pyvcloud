# Installation 

`pyvcloud` requires Python 3.  See sections below for installation on
major OS distributions. Examples consistently use `pip3 install --user`
to install Python 3 modules privately to each OS account.  This command
ensures proper operation when there are mixed Python versions.  It also
avoids changes to the default Python installation.  Another approach is
to use virtualenv (see below).

Note that there are a couple of confusing exceptions related to installing
`pip` itself. In these cases you **must** use the name `pip`.

Pre-release and source installations are covered at the end of the page,
so keep reading to experience life on the bleeding edge.

If you find a bug in these procedures please file an issue or submit
a pull request as described in [CONTRIBUTING.md](../CONTRIBUTING.md).

## Ubuntu

Ubuntu 16.04:
``` shell
    $ sudo apt-get install python3-pip gcc -y
    $ pip3 install --user pyvcloud
```

**Note:** If you encounter wheel errors ensure your pip3 version is up
to date.  ```pip3 install --upgrade pip``` usually fixes them.

## CentOS

```shell
    $ sudo yum update
    $ sudo yum install -y yum-utils
    $ sudo yum groupinstall -y development
    $ sudo yum -y install https://centos7.iuscommunity.org/ius-release.rpm
    $ sudo yum -y install python36u python36u-pip python36u-devel
    $ sudo easy_install-3.6 pip
    $ pip3 install --user pyvcloud
```

## Photon OS 

Photon OS minimal installs lack standard tools like pip3 and even ping,
so you need to install a number of packages using tdnf.  There are also
differences between Photon 1 and 2 distributions, so setup differs.

Photon 1:
``` shell
    $ tdnf install -y gcc glibc-devel glibc-lang binutils python3-devel linux-api-headers
    $ pip3 install --user pyvcloud
```

Photon 2:
``` shell
    $ tdnf install -y build-essential python3-setuptools python3-tools python3-pip python3-devel
    $ pip3 install --user pyvcloud
```

## Mac OS X

Open a Terminal and enter the commands listed below.  Skip those that
refer to a component already installed on your Mac. 

Install `Xcode Command Line Tools`:
``` shell
    $ xcode-select --install
```
Press `Install` and accept the license terms.

Install `pip3`:
``` shell
    $ sudo easy_install pip
```
Install `pyvcloud`:
``` shell
    $ pip3 install --user pyvcloud
```

**Note**: Python installations on Mac OS X sometimes have problems with
library compatibilities.  Here are known issues and fixes.

Newer Python versions including 3.6.4 may experience path issues or SSL
cert failures when running pip3.  To get past them ensure your path
points to the installed Python executables and not just the links in
/usr/local/bin. Also, ensure that the pbr module is up to date.  Here is
an example.  Your installation location may vary, so check to be sure.
``` shell
    $ export PATH=/Library/Frameworks/Python.framework/Versions/3.6/bin:$PATH
    $ pip3 install --user pbr
```

Older Mac OS X Python3 versions link with an outdated OpenSSL
library, which may lead to failures.  If you get SSL errors on login,
try adding the following libraries, then run pip3 again.
``` shell
    $ pip3 install --user urllib3 pyopenssl
```

## Windows 10

Start by installng Python 3 using the latest Windows installer available from 
https://www.python.org/downloads/windows/ and ensure that python.exe is in 
the path.  

Install `pyvcloud` and add to the PATH (needed for local installs):
``` shell
    C:\Users\Administrator>pip3 install --user pyvcloud
    C:\Users\Administrator>set PATH=%PATH%;C:\Users\Administrator\AppData\Roaming\Python\Python36\Scripts
```

Administrator is just an example.  Other accounts work as well. 

## Verify Installation

Run the system-info.py script in the examples directory:  
``` shell
    $ cd examples
    $ ./system-info.py 10.150.202.222 Org1 user1 mypassword
    Logging in: host=10.150.202.222, org=Org1, user=user1
    Fetching vCD installation info...
    Key: name Value: VMware vCloud Director
    Key: href Value: https://10.150.202.222/api/admin/
    Key: type Value: application/vnd.vmware.admin.vcloud+xml
    Logging out
```
The host, org, user, and password values should be specific to your
vCD installation.

## Installation with virtualenv

It is also possible to install `pyvcloud` in a [virtualenv](https://docs.python.org/3/library/venv.html).  Quick commands to do so:
``` shell
    $ python3 -m venv $HOME/my_venv
    $ . $HOME/my_venv/bin/activate
    (my_venv) $ pip3 install pyvcloud
```
To terminate the virtual environment use the `deactivate` command. In
this case we don't use the --user option as venv supplies its own location
for packages.  Adding the --user option may cause odd installation behavior on
some platforms.

## Upgrade

To upgrade an existing `pyvcloud` install, run:

``` shell
    $ pip3 install --user pyvcloud --upgrade
```

## Pre-releases

The commands described above install the current stable version of `pyvcloud`. 
To install a pre-release version, enter:

``` shell
    $ pip3 install --user pyvcloud --pre
```

And to upgrade a pre-release:

``` shell
    $ pip3 install --user pyvcloud --pre --upgrade
```

Installation from the current development version in GitHub:

``` shell
    $ pip3 install --user git+https://github.com/vmware/pyvcloud.git
```

Install specific Github or published versions:

``` shell
    $ pip3 install --user git+https://github.com/vmware/pyvcloud.git@19.1.0
    (or)
    $ pip3 install --user pyvcloud==19.1.0
```

## Installation from Local Source Files

This is the standard installation for development.  Clone the code and
install from source.
``` shell
    $ git clone https://github.com/vmware/pyvcloud.git
    $ cd pyvcloud
    $ python3 setup.py develop
```
Scripts will automatically pick up current pyvcloud source files including
any changes you have made.  Use of virtualenv is recommended to avoid
polluting your regular Python installation.

**Note:** You may need additional libraries for pyvcloud development. 
The following command installs extra dev libraries required on Ubuntu 16.04. 
``` shell
    sudo apt-get install libxml2-dev libxslt-dev zlib1g-dev
```
