#!/bin/bash

vca login $VCA_CLI_USER --password $VCA_CLI_PASSWORD --instance $VCA_CLI_INSTANCE
vca status
