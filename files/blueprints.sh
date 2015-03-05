#!/bin/bash

#sample commands to work with blueprints

ORGID=`vca -j org info| jq -r '.orgs[0].Name'` && echo ${ORGID}
vca bp upload --blueprint ${ORGID}_bp1 --file blueprint/blueprint.yaml
vca bp
vca dep create --blueprint ${ORGID}_bp1 --deployment ${ORGID}_dp1 --file input.json
vca dep
vca dep info --deployment ${ORGID}_dp1
vca dep execute --deployment ${ORGID}_dp1 --workflow install
vca dep info --deployment ${ORGID}_dp1
vca dep execute --deployment ${ORGID}_dp1 --workflow uninstall
vca dep delete --deployment ${ORGID}_dp1
