#!/bin/bash 
if [ x$1=x"precustomization" ]; 
then 

mkdir -p /home/ubuntu/.ssh

echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC/nPd1ZlLC60sWWj7SEmmqn5u6AAKkNmt90YTOxlmJdVZyA8+9/II11QHURlwTk5+F4km+xZwvFst1V21SerutAAVsFKFnxG02m9pPhu+WUbPiLs4MAFMLbBlEZjqp7Tpx0IT3leONQ2s7JtDZ8A/urvzZy941AZx3m7P/OlUeNNU5elxHtrXgJ1aWdK5/dRtF2bUZqM5fnxx3Xgyhp/+a1frtvb4oqRV88hYw4GhOBZgfx9WubrjO+VAu7Ogg5DJuIC8VSnk7pPJ5qI4vGa5CNomA1jd3MjbH5FfmOI4sMX9RG70uYT13K2UkIVXWeGdZlAb7UaDurgJQVQviCDB9 foo@bar' >> /home/ubuntu/.ssh/authorized_keys
echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDFlYX8JkGVKtCUmSi4NStzT+qCqRuFaqP6gzxly7atmfGTXGymOwf56mP9j1vM4a5OLSwTS/xQb9RrHPWZmohqApvaIyM9MQTF1EkoPtb39/tLDyWiAS/czXMGx2VWCqRAfZhdoUn1pd14hyfCUDqDv0Guo3Z/VF5dqHVSB0dHgjNeAYCsWXQhtm+GBxBUxohGaPNzO6wQZvhOnJT2KaVDDlZa3SsK1s+Lx0YDW3s2AkB759dRi71m/kFQBBcXSo2lqg6hRDCgbO6xtVcw/fi3IGsOVTXeZW2dwDq3B10AZZcrsQJAGrIXtVDw2LPnf0hISQkVV43ZNE4Aa5OEPQ5T manager' >> /home/ubuntu/.ssh/authorized_keys

chown ubuntu.ubuntu /home/ubuntu/.ssh
chown ubuntu.ubuntu /home/ubuntu/.ssh/authorized_keys
chmod go-rwx /home/ubuntu/.ssh
chmod go-rwx /home/ubuntu/.ssh/authorized_keys

fi 