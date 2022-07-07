#!/usr/bin/env bash

cd $(dirname $0)

echo "==> Adding links to captions in left TOC"
python3 ../python/add_toc_caption_links.py
