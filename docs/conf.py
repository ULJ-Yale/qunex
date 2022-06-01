# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
import datetime

# These directories are specified in order to make Sphinx structure
# modules from Python files at the same level as MATLAB folders, e.g.:
# * Python: qx_utilities.general.fidl.check_fidl
# * MATLAB: qx_utilities.general.general_check_file
# This way they both share qx_utilities.general.
sys.path.append(os.path.abspath('../python'))
sys.path.append(os.path.abspath('../python/qx_utilities'))
sys.path.append(os.path.abspath('../matlab/qx_utilities'))
# See 'Options for MATLAB domain extension' section for additional path to
# MATLAB files


# -- Project information -----------------------------------------------------

project = 'QuNex'
copyright = f'{str(datetime.date.today().year)}, Anticevic Lab (Yale University), Mind and Brain Lab (University of Ljubljana), Murray Lab (Yale University)'

version_path = "../VERSION.md"
# check if file exists to avoid error when using this script as import
if os.path.isfile(version_path):
    with open(version_path, "r") as version_file:
        # The full version, including alpha/beta/rc tags
        release = version_file.read()

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinxcontrib.matlab',
#    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'recommonmark',
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


# -- Options for MATLAB domain extension -------------------------------------

matlab_src_dir = os.path.abspath('../matlab')


# -- Options for Napoleon extension ------------------------------------------

# Google style is used throughout the project, so NumPy style can be ignored
napoleon_numpy_docstring = False

# The heading 'Specific parameters' is not part of the default Napoleon set of
# section headings, so it has been added manually. (list is not case-sensitive)
napoleon_custom_sections = [
    ('specific parameters', 'params_style'),
    ('output files'),
]


# -- Options for Opengraph extension -----------------------------------------

# TODO: change ogp_site_url to "docs.qunex.yale.edu" or other actual URL
ogp_site_url = "https://featuredocs.readthedocs.io/"
ogp_image = "https://bytebucket.org/oriadev/qunex/wiki/Images/QuNex_Logo_small.png"


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
]

html_title = f'{project} documentation'

#html_logo = 'wiki/Images/QuNex_Logo_small.png'
html_favicon = '_static/img/favicon.png'

html_theme_options = {
    "home_page_in_toc": True
}
