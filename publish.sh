#!/usr/bin/env bash

./cleanup.sh
python setup.py develop
python setup.py sdist bdist_wheel
twine upload dist/*
