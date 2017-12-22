#!/usr/bin/env bash

set -e

D=`dirname $0`
$D/tenant-onboard.sh
$D/tenant-operations.sh
$D/cleanup.sh
