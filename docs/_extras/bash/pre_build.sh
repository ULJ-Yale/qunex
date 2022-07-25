#!/usr/bin/env bash

cd $(dirname $0)

echo "==> Cloning latest wiki version from GitLab"
git clone --depth 1 https://token:glpat-rjavmB_di2fsZCtqHzYi@gitlab.qunex.yale.edu/qunex/qunex.wiki.git ../../wiki

echo "==> Removing [TOC] from wiki files"
find ../../wiki -iname '*.md' -exec sed -i.bkp '/\[TOC\]/d' '{}' ';'
find ../../wiki -name "*.bkp" -type f -delete

echo "==> Converting Home.md to index.rst and HomeMenu.rst"
python3 ../python/generate_index.py

echo "==> Generating Python-like docstrings from unsupported (bash and R) commands"
python3 ../python/extract_unsupported_docstrings.py

echo "==> Generating .rst files for individual commands"
python3 ../python/generate_gmri_rsts.py

# use the following command to build the documentation locally from $QUNEXPATH/docs:
# python3 -m sphinx -T -E -b html -d _build/doctrees -D language=en . _build/html