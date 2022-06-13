#!/usr/bin/env python3
# encoding: utf-8

"""
Warning:
    This script cannot work because Read the Docs copies files to another
    temporary location that is not accessible to users. Changing HTML files
    post build is thus not yet possible
    (see https://github.com/readthedocs/readthedocs.org/issues/9172).

It adds hyperlinks to those captions in the left table of contents that also
have hyperlinks in the Home.md file.
"""

import os
import re


def list_html_files(path):
    html_files = []
    for root, dirs, files in os.walk(path):
        for file_path in files:
            if file_path.endswith(".html"):
                html_files.append(os.path.abspath(os.path.join(root, file_path)))
    return html_files


def replace_span(heading, replacement, string_contents):
    return re.sub(r'<span class=\"caption-text\">.*\n?.*' + heading + r'.*\n?.*</span>', replacement, string_contents)


def relative_path(path_from, path_to):
    return os.path.relpath(path_to, start=os.path.dirname(path_from))


# hardcoded (already included in TOC via Sphinx .rst)
headings_to_ignore = ["QuNex quick start"]

dirname = os.path.dirname(__file__)
path_to_mds = os.path.abspath(os.path.join(dirname, '..', '..', 'wiki'))
path_to_home = os.path.join(path_to_mds, 'Home.md')
path_to_htmls = os.path.abspath(os.path.join(dirname, '..', '..', '_build', 'html'))
path_to_wiki_htmls = os.path.join(path_to_htmls, "wiki")

headings_html = []

with open(path_to_home, "r") as home_file:
    home_contents = home_file.read()
    headings = re.findall("\n## \[(.*)\]\((.*)\).*\n", home_contents)

# links only the currently active heading
for name, link in headings:
    if name not in headings_to_ignore:
        link = re.sub(r"\.md", ".html", link)

        headings_html.append((name, link))

        path_to_file = os.path.join(path_to_htmls, "wiki", link)
        replacement_code = f'<a class="reference internal active" href="#">\n    {name}\n</a>'

        with open(path_to_file, 'r') as old_file:
            file_contents = old_file.read()
            new_contents = replace_span(name, replacement_code, file_contents)

        with open(path_to_file, 'w') as new_file:
            new_file.write(new_contents)

# links headings that are not currently active
for path_to_html in list_html_files(path_to_htmls):
    for name, link in headings_html:
        relative_link = relative_path(path_to_html, os.path.join(path_to_wiki_htmls, link))

        replacement_code = f'<a class="reference internal" href="{relative_link}">\n    {name}\n</a>'

        with open(path_to_html, 'r') as old_file:
            file_contents = old_file.read()
            new_contents = replace_span(name, replacement_code, file_contents)

        with open(path_to_html, 'w') as new_file:
            new_file.write(new_contents)
