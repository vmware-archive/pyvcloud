#!/usr/bin/env bash
set -e

SHOME=`dirname $0`
cd $SHOME

SRCROOT=`cd ..; pwd`
cd $SRCROOT

VIRTUAL_ENV_DIR=${VIRTUAL_ENV_DIR:-auto.env}

python3 --version

rm -rf $VIRTUAL_ENV_DIR
python3 -m venv $VIRTUAL_ENV_DIR

. $VIRTUAL_ENV_DIR/bin/activate
pip3 install -r requirements.txt
python3 setup.py install