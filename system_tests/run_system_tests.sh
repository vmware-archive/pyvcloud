#!/bin/bash
# 
# Script to run all system tests. 
#
# Usage: ./run_system_tests.sh [vcd_connection_file]
#
# where vcd_connection_file sets environmental variables to define the vCD 
# server connection. See vcd_connection.sample for an example. 
#
set -e
SCRIPT_DIR=`dirname $0`

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

# Prepare a test parameter file. We'll use sed to replace values and create 
# a new file.  Note that some environmental variables may not be set in which
# case the corresponding parameter will end up an empty string. 
sed -e "s/<vcd ip>/${VCD_HOST}/" \
-e "s/30.0/${VCD_API_VERSION}/" \
-e "s/\(sys_admin_username: \'\)administrator/\1${VCD_USER}/" \
-e "s/<root-password>/${VCD_PASSWORD}/" \
< ${SCRIPT_DIR}/base_config.yaml > test.base_config.yaml

# Run the tests with the new file. From here on out all commands are logged. 
set -x
export VCD_TEST_BASE_CONFIG_FILE=${SCRIPT_DIR}/test.base_config.yaml
python3 -m unittest idisk_tests.py
