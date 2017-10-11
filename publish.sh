#!/usr/bin/env bash

rm -rf vcd_cli/*.pyc
rm -rf build dist
python setup.py develop
python setup.py sdist bdist_wheel
twine upload dist/*
