#!/usr/bin/env bash

set -e

vcd version

VCD_HOST=bos1-vcd-sp-static-202-34.eng.vmware.com
VCD_ORG=org5
VCD_USER=usr1
VCD_PASSWORD=ca\$hc0w
VDC=vdc1

vcd login $VCD_HOST $VCD_ORG $VCD_USER --password $VCD_PASSWORD -w -i --vdc $VDC

vcd vdc list
vcd vapp create vapp1
vcd vapp list
vcd catalog create cat1
vcd catalog list

echo 'this will result in error because the vapp has no VM, can be ignored'
vcd vapp capture vapp1 cat1 template1

vcd catalog list cat1

vcd catalog delete cat1 template1 --yes
vcd catalog delete cat1 --yes
vcd vapp delete vapp1 --yes
vcd logout
