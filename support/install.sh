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
    run_in_docker support/install.sh
else
    python3 --version

    rm -rf $PYVCLOUD_VENV_DIR
    python3 -m venv $PYVCLOUD_VENV_DIR

    . $PYVCLOUD_VENV_DIR/bin/activate
    pip3 install -r requirements.txt
    python3 setup.py install
fi