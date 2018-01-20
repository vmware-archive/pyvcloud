#!/usr/bin/env bash

yapf -i pyvcloud/vcd/*.py
flake8 pyvcloud/vcd/*.py
