#!/bin/bash
# Copyright (c) 2018 VMware, Inc. All Rights Reserved.
#
# This product is licensed to you under the
# Apache License, Version 2.0 (the "License").
# You may not use this product except in compliance with the License.
#
# This product may include a number of subcomponents with
# separate copyright notices and license terms. Your use of the source
# code for the these subcomponents is subject to the terms and
# conditions of the subcomponent's license, as noted in the LICENSE file.

# Script to run all system tests.
#
# Usage: ./run_system_tests.sh [test1.py test2.py ...]
#
# If you give test names we'll run them.  Otherwise it defaults
# to the current stable tests.
#
# The script requires a vcd_connection file which defaults to
# $HOME/vcd_connection.  See vcd_connection.sample for an example.
# You can also set it in the VCD_CONNECTION environmental variable.
#
set -e

cd `dirname $0`
SCRIPT_DIR=`pwd`
SRCROOT=`cd ..; pwd`
cd $SRCROOT

# If there are tests to run use those. Otherwise use stable tests.
STABLE_TESTS="client_tests.py \
api_extension_tests.py \
catalog_tests \
extnet_tests.py \
gateway_tests.py \
idisk_tests.py \
network_tests.py \
org_tests.py \
search_tests.py \
vapp_tests.py \
vdc_tests.py \
vm_tests.py"

if [ $# == 0 ]; then
  echo "No tests provided, will run stable list: ${STABLE_TESTS}"
  TESTS=$STABLE_TESTS
else
  TESTS=$*
fi

# Get connection information.
if [ -z "$VCD_CONNECTION" ]; then
  VCD_CONNECTION=$HOME/vcd_connection
fi

if [ -f $VCD_CONNECTION ]; then
    echo "Using default vcd_connection file location: $VCD_CONNECTION"
else
  echo "Must set valid VCD_CONNECTION or define $HOME/vcd_connection"
  exit 0
fi
. "$VCD_CONNECTION"

# Prepare a test parameter file. We'll use sed to replace values and create
# a new file.  Note that some environmental variables may not be set in which
# case the corresponding parameter will end up an empty string.
auto_base_config=$SRCROOT/auto.base_config.yaml
sed -e "s/<vcd ip>/${VCD_HOST}/" \
-e "s/30.0/${VCD_API_VERSION}/" \
-e "s/\(sys_admin_username: \'\)administrator/\1${VCD_USER}/" \
-e "s/<root-password>/${VCD_PASSWORD}/" \
-e "s/<vc ip>/${VC_IP}/" \
-e "s/<vc root password>/${VC_PASSWORD}/" \
-e "s/<vc2 ip>/${VC2_IP}/" \
-e "s/<vc2 root password>/${VC2_PASSWORD}/" \
< ${SRCROOT}/system_tests/base_config.yaml > ${auto_base_config}
echo "Generated parameter file: ${auto_base_config}"

# Detect if a Python virtualenv is already active
if [ -z "$VIRTUAL_ENV" ]; then
    # Load virtualenv if $VIRTUAL_ENV_DIR is set
    if [ -n "$VIRTUAL_ENV_DIR" ]; then
        . $VIRTUAL_ENV_DIR/bin/activate
    fi
fi

cd system_tests

# Run the tests with the new file. From here on out all commands are logged.
set -x
export VCD_TEST_BASE_CONFIG_FILE=${auto_base_config}
python3 main.py $TESTS
