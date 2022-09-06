#!/usr/bin/env bash

cd $(dirname $0)

echo "==> Cloning latest wiki version from GitLab"
git clone --depth 1 https://token:glpat-rjavmB_di2fsZCtqHzYi@gitlab.qunex.yale.edu/qunex/qunex.wiki.git ../../wiki
#cp -r ../../../../qunex.wiki ../../wiki  # useful during development

echo "==> Removing [TOC] from wiki files"
find ../../wiki -iname '*.md' -exec sed -i.bkp '/\[TOC\]/d' '{}' ';'
find ../../wiki -name "*.bkp" -type f -delete

python3 ../python/generate_index.py

python3 ../python/extract_unsupported_docstrings.py

python3 ../python/generate_gmri_rsts.py

# use the following command to build the documentation locally from $QUNEXPATH/docs:
# python3 -m sphinx -T -E -b html -d _build/doctrees -D language=en . _build/html