#!/usr/bin/env bash
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

SHOME=`dirname $0`
cd $SHOME

SRCROOT=`cd ..; pwd`
cd $SRCROOT

# Initialize the PYTHON3_IN_DOCKER variable and
# load methods for interacting with Docker
. ./support/lib.sh

# Initialize the VCD_CONNECTION variable
set_vcd_connection

if [ "$PYTHON3_IN_DOCKER" != "0" ]; then
    run_in_docker system_tests/run_system_tests.sh $*
else
    # If there are tests to run use those. Otherwise use stable tests. 
    STABLE_TESTS="client_tests.py \
    idisk_tests.py \
    search_tests.py \
    vapp_tests.py \
    catalog_tests"

    if [ $# == 0 ]; then
        echo "No tests provided, will run stable list: ${STABLE_TESTS}"
        TESTS=$STABLE_TESTS
    else
        TESTS=$*
    fi

    # Detect if a Python virtualenv is already active
    if [ -z "$VIRTUAL_ENV" ]; then
        . $PYVCLOUD_VENV_DIR/bin/activate
    fi
    . "$VCD_CONNECTION"

    # Prepare a test parameter file. We'll use sed to replace values and create 
    # a new file.  Note that some environmental variables may not be set in which
    # case the corresponding parameter will end up an empty string. 
    auto_base_config=${SRCROOT}/system_tests/auto.base_config.yaml
    sed -e "s/<vcd ip>/${VCD_HOST}/" \
    -e "s/30.0/${VCD_API_VERSION}/" \
    -e "s/\(sys_admin_username: \'\)administrator/\1${VCD_USER}/" \
    -e "s/<root-password>/${VCD_PASSWORD}/" \
    < ${SRCROOT}/system_tests/base_config.yaml > ${auto_base_config}
    echo "Generated parameter file: ${auto_base_config}"

    # Run the tests with the new file. From here on out all commands are logged. 
    set -x
    export VCD_TEST_BASE_CONFIG_FILE=${auto_base_config}

    cd $SRCROOT/system_tests
    python3 -m unittest $TESTS -v
fi
