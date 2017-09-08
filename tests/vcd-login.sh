#!/usr/bin/env bash

set -e
vcd -j login $VCD_HOST $VCD_ORG $VCD_USER --password $VCD_PASSWORD -w -i
