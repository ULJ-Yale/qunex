# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import os
import sys
import datetime

sys.path.append(os.path.join("..", "python"))
matlab_src_dir = os.path.join("..", "matlab")  # MATLAB domain root folder

# Modules or directories that are shared between multiple languages (e.g.
# qx_utilities) have to be added to sys.path separately for each language.
for lang in ["python", "matlab"]:
    path_with_modules = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", lang))
    if os.path.isdir(path_with_modules):
        for each in os.listdir(path_with_modules):
            full_path = os.path.join(path_with_modules, each)
            if os.path.isdir(full_path):
                sys.path.append(os.path.abspath(full_path))

# -- Project information -----------------------------------------------------

project = 'QuNex'
copyright = f'{str(datetime.date.today().year)}, Anticevic Lab (Yale University), Mind and Brain Lab (University of Ljubljana), Murray Lab (Yale University)'

version_path = "../VERSION.md"
# check if file exists to avoid error when using this script as import
if os.path.isfile(version_path):
    with open(version_path, "r") as version_file:
        # The full version name, including alpha/beta/rc tags
        release = version_file.read()

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinxcontrib.matlab',
#    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'myst_parser',
    'sphinx_copybutton',
    'sphinxext.opengraph',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# Disabled to allow for "normal" interpretation of double dashes (--),
# ellipses (...) etc.
smartquotes = False

# -- Options for Napoleon extension ------------------------------------------

# Google style is used throughout the project, so NumPy style can be ignored
napoleon_numpy_docstring = False

napoleon_custom_sections = [
    ('parameters'),
    ('returns'),
    ('output files'),
]

# -- Options for MyST parser extension --------------------------------------
# Depth of auto-generated header anchors
myst_heading_anchors = 4

# -- Options for Opengraph extension -----------------------------------------

ogp_site_url = "https://qunex.readthedocs.io/"
ogp_image = "https://qunex.readthedocs.io/en/latest/_images/QuNex_Logo_pantheonsite.png"

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#

html_theme = 'sphinx_book_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_css_files = [
    'css/custom.css',
    'css/header.css',
]

html_js_files = [
    'js/header.js',
    'js/custom.js',
]

html_title = f'{project} documentation'

#html_logo = 'wiki/Images/QuNex_Logo_small.png'
html_favicon = '_static/img/favicon.png'

html_theme_options = {
    "home_page_in_toc": True
}
