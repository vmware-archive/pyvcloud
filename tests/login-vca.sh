#!/bin/bash

set -e
vca logout
vca login $VCA_CLI_USER --password $VCA_CLI_PASS --instance $VCA_CLI_INSTANCE
vca status
