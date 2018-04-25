#!/bin/bash
# 
# Script to run all samples in order. 
#
# Usage: ./run_samples.sh [vcd_connection_file]
#
# where vcd_connection_file sets environmental variables to define the vCD 
# server connection. See vcd_connection.sample for the format. 
#
set -e

# Get connection information.  If provided the file name must be absolute. 
VCD_CONNECTION=$1
if [ -z "$VCD_CONNECTION" ]; then
  VCD_CONNECTION=$HOME/vcd_connection
  if [ -e $HOME/vcd_connection ]; then
    echo "Using default vcd_connection file location: $VCD_CONNECTION"
  else
    echo "Must have $VCD_CONNECTION or give alternative file as argument"
    exit 0
  fi
fi
. "$VCD_CONNECTION"

# Prepare a sample tenant yaml file by cat'ing so that environment variables
# fill in. 
SCRIPT_DIR=`dirname $0`
eval "cat <<EOF
$(<$SCRIPT_DIR/tenant.yaml)
EOF
" 2> /dev/null > sample-test-tenant.yaml

# From here on out all commands are logged. 
set -x
python3 ${SCRIPT_DIR}/system-info.py ${VCD_HOST} ${VCD_ORG} ${VCD_USER} ${VCD_PASSWORD}
python3 ${SCRIPT_DIR}/tenant-remove.py sample-test-tenant.yaml
python3 ${SCRIPT_DIR}/tenant-onboard.py sample-test-tenant.yaml
python3 ${SCRIPT_DIR}/list-vapps.py ${VCD_HOST} Test1 user1 secret VDC-A
python3 ${SCRIPT_DIR}/list-vdc-resources.py ${VCD_HOST} Test1 user1 secret
