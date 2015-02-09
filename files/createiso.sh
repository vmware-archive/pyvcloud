#!/bin/bash

# Hostname of CoreOS Instance
CORE_OS_HOSTNAME=coreos1

# IP Address of CoreOS Instance
CORE_OS_IP_ADDRESS=192.168.109.2

# IP Address of the gateway
CORE_OS_IP_GW=192.168.109.1

# Username to enable on CoreOS Instance
CORE_OS_USERNAME=vcauser

CORE_OS_AUTHORIZED_KEYS='AAAAB3NzaC1yc2EAAAADAQABAAABAQC3ZGXfIeoNoAiKBTeEaBnyaPFofi2MifxIvMQEYU0yOIUMWsdc4tGCXDbL1kz6ApQN+KLN3m1mpP5MHTEaDwt7QqiFom6c3Zb0wE7EaEl9paT1K2ApgEQAjR8q5km03S50vXmVjPF8on5caCqcnOqgSm9xekZvpVNykgbVJ2POyFeTCaG5ho7HEok4H3j0gwpDnNPeEJkVUlNrsfEGf2AAwHbxt9SG8QnBjMwdSLGI1HjCBK/4n11ADMEXJiwL+n7WvWtrymCrNHGsgymvFI7sq9unJCzpQ02SNl66wvmZPPrrezWg9WxsAxXeuL+bHXuFfCYSFO3mSPbsTTcjqVnH'

# Name of the CoreOS Cloud Config ISO
CLOUD_CONFIG_ISO=${CORE_OS_HOSTNAME}-config.iso

TMP_CLOUD_CONFIG_DIR=/tmp/new-drive

echo "Build Cloud Config Settings ..."
mkdir -p ${TMP_CLOUD_CONFIG_DIR}/openstack/latest

cat > ${TMP_CLOUD_CONFIG_DIR}/openstack/latest/user_data << __CLOUD_CONFIG__
#cloud-config

hostname: ${CORE_OS_HOSTNAME}

write_files: 
  - path: /etc/systemd/network/static.network 
    permissions: 0644 
    content: | 
      [Match] 
      Name=en*
      [Network] 
      Address=${CORE_OS_IP_ADDRESS}/24 
      Gateway=${CORE_OS_IP_GW}
      DNS=8.8.8.8

coreos:
  units:
    - name: systemd-networkd.service
      command: start

users:
  - name: ${CORE_OS_USERNAME}
    primary-group: wheel
    groups:
      - sudo
      - docker
    ssh-authorized-keys:
      - ssh-rsa ${CORE_OS_AUTHORIZED_KEYS}

__CLOUD_CONFIG__

echo "Creating Cloud Config ISO ..."
mkisofs -R -V config-2 -o ${CLOUD_CONFIG_ISO} ${TMP_CLOUD_CONFIG_DIR}

