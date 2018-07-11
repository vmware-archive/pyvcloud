#!/usr/bin/env bash
#
# Activate the Python virtualenv directory and run
# code style checks on the pyvcloud project
#
# If a virtualenv is already active, it will be used instead
# of activating a new one. The $VIRTUAL_ENV_DIR variable
# may be used to specify the virtualenv to use.
#
set -e

SHOME=`dirname $0`
cd $SHOME

SRCROOT=`cd ..; pwd`
cd $SRCROOT

# Detect if a Python virtualenv is already active
if [ -z "$VIRTUAL_ENV" ]; then
    # Load virtualenv if $VIRTUAL_ENV_DIR is set
    if [ -n "$VIRTUAL_ENV_DIR" ]; then
        . $VIRTUAL_ENV_DIR/bin/activate
    fi
fi

pip3 install -r test-requirements.txt
tox -e flake8