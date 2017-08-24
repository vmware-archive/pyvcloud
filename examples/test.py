#! /usr/bin/env python

from fabric.api import env, run, execute
from fabric import network
from fabric.context_managers import settings

def host_type():
    with settings(prompts={"(current) UNIX password: ": "changeme", "New password: ": "my_secure_password", "Retype new password: ": "my_secure_password"}):
        result = run('uname -a')
    return result

if __name__ == '__main__':
    print ("Fabric v%(version)s" % env)
    env.user = 'root'
    env.password = 'my_secure_password'
    env.hosts = ['192.168.3.231']
    host_types = execute(host_type)
