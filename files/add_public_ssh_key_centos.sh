#!/bin/bash 

mkdir -p /root/.ssh

echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC/nPd1ZlLC60sWWj7SEmmqn5u6AAKkNmt90YTOxlmJdVZyA8+9/II11QHURlwTk5+F4km+xZwvFst1V21SerutAAVsFKFnxG02m9pPhu+WUbPiLs4MAFMLbBlEZjqp7Tpx0IT3leONQ2s7JtDZ8A/urvzZy941AZx3m7P/OlUeNNU5elxHtrXgJ1aWdK5/dRtF2bUZqM5fnxx3Xgyhp/+a1frtvb4oqRV88hYw4GhOBZgfx9WubrjO+VAu7Ogg5DJuIC8VSnk7pPJ5qI4vGa5CNomA1jd3MjbH5FfmOI4sMX9RG70uYT13K2UkIVXWeGdZlAb7UaDurgJQVQviCDB9 foo@bar' >> /root/.ssh/authorized_keys

chmod go-rwx /root/.ssh
chmod go-rwx /root/.ssh/authorized_keys
restorecon -Rv /root/.ssh

#password:
#vca -x vapp info --vapp cen | grep "AdminPassword>"

#echo 'DNS1=8.8.8.8' >> /etc/sysconfig/network-scripts/ifcfg-eth1

