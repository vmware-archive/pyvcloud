#!/bin/bash

export USERID=email@company.com
export PASSWORD=my_password
export INSTANCEID=37d9e482-a5d1-4811-b466-c4d1e2f67f2c
export VDC=VDC1

vca logout
#on demand login
vca login $USERID --password $PASSWORD --save-password --instance $INSTANCEID

sleep 2

vca vdc use --vdc $VDC

for n in {1..9} 
do 
    vca vapp create --vapp myvapp-${n} --vm myvm --catalog 'Public Catalog' --template 'CentOS64-64BIT' --network 'default-routed-network' --mode POOL
done
