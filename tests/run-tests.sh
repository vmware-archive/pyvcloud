#!/usr/bin/env bash

# use VCD_TEST_CONFIG_FILE to set your private config.yml file

python -m unittest \
  vcd_login \
  vcd_catalog_setup \
  vcd_catalog \
  vcd_vdc \
  vcd_vapp \
  vcd_catalog_teardown
