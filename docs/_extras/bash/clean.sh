#!/usr/bin/env bash

cd $(dirname $0)

echo "==> Cleaning docs and related directories"
rm -rf ../../wiki ../../HomeMenu.rst ../../index.rst ../../_build
rm -f ../../api/gmri/*
rm -rf  ../../../python/qx_utilities/bash.py ../../../python/qx_utilities/r.py
