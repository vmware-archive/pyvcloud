#!/usr/bin/env bash
set -e

SHOME=`dirname $0`
cd $SHOME

SRCROOT=`cd ..; pwd`
cd $SRCROOT

# Initialize the PYTHON3_IN_DOCKER variable and
# load methods for interacting with Docker
. ./support/lib.sh

if [ "$PYTHON3_IN_DOCKER" != "0" ]; then
    run_in_docker support/tox.sh
else
    # Detect if a Python virtualenv is already active
    if [ -z "$VIRTUAL_ENV" ]; then
        . $PYVCLOUD_VENV_DIR/bin/activate
    fi
    
    pip3 install -r test-requirements.txt
    tox -e flake8
fi