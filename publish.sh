#!/usr/bin/env bash

rm -rf pyvcloud/vcd/*.pyc
rm -rf build dist
python setup.py develop
python setup.py sdist bdist_wheel
twine upload dist/*
