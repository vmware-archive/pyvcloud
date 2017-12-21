#!/usr/bin/env bash

set -e

VCD_HOST=bos1-vcd-sp-static-202-34.eng.vmware.com
VCD_ORG=System
VCD_USER=Administrator
VCD_PASSWORD=ca\$hc0w

vcd login $VCD_HOST $VCD_ORG $VCD_USER --password $VCD_PASSWORD -w -i

ORG=org5
VDC=vdc1

vcd org use $ORG
vcd vdc list
vcd vdc disable $VDC
vcd vdc delete $VDC --yes
vcd org update $ORG --disable
vcd org delete $ORG --yes
vcd org list
vcd logout
