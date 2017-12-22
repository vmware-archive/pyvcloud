#!/usr/bin/env bash

set -e

vcd version

VCD_HOST=bos1-vcd-sp-static-202-34.eng.vmware.com
VCD_ORG=System
VCD_USER=Administrator
VCD_PASSWORD=ca\$hc0w

vcd login $VCD_HOST $VCD_ORG $VCD_USER --password $VCD_PASSWORD -w -i

ORG=org5
USR=usr1
VDC=vdc1

vcd org list
vcd org create $ORG 'Test Organization Five' --enabled
vcd org list
vcd org use $ORG
vcd role list
vcd user create $USR ca\$hc0w 'Organization Administrator' --enabled
vcd pvdc list
vcd netpool list
vcd vdc create $VDC -p pvdc-2017-11-28-14-47-16.712 -n pvdc-2017-11-28-14-47-16.712-VXLAN-NP -s \*
