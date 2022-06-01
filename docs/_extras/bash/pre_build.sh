#!/usr/bin/env bash

cd $(dirname $0)

echo "==> Cloning latest wiki version from BitBucket"
git clone --depth 1 https://bitbucket.org/oriadev/qunex.git/wiki ../../wiki

echo "==> Removing [TOC] from wiki files"
find ../../wiki -iname '*.md' -exec sed -i.bkp '/\[TOC\]/d' '{}' ';'
find ../../wiki -name "*.bkp" -type f -delete

echo "==> Converting Home.md to index.rst and HomeMenu.rst"
python3 ../python/generate_index.py

echo "==> Generating Python-like docstrings from unsupported (bash and R) commands"
python3 ../python/extract_unsupported_docstrings.py

echo "==> Generating .rst files for individual commands"
python3 ../python/generate_gmri_rsts.py
