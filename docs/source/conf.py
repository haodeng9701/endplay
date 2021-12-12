# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

import sys
from pathlib import Path
from distutils.dir_util import copy_tree

sourcedir = Path(__file__).parent.resolve()
docsdir = sourcedir.parent
builddir = docsdir / "build"
basedir = docsdir.parent

# Allow finding of modules for building docs
sys.path.insert(0, str(sourcedir / "modules"))

# If we are an insource build, then append the src dir to path
if tags.has("insource"):
	srcdir = basedir / "src"
	sys.path.insert(0, str(srcdir))

# If the cleanpages tag is passed, then delete all the generated pages
if tags.has("cleanpages") and (sourcedir / "pages").exists():
	print("Cleaning pages directory...")
	import shutil
	shutil.rmtree(sourcedir / "pages")


# -- Project information -----------------------------------------------------

project = 'endplay'
copyright = '2021, Dominic Price'
author = 'Dominic Price'

# Import endplay. 
import endplay
print("Using build located at", endplay.__path__[0])
release = endplay.__version__


# -- General configuration ---------------------------------------------------

extensions = [
	'sphinxcontrib.apidoc',
	'sphinx.ext.autodoc',
	'myst_parser',
	'autodoc_rename',
	'parse_readme',
	'autodocsumm',
	'generate_index'
]

# apidoc
apidoc_module_dir = endplay.__path__[0]
apidoc_output_dir = str(sourcedir / "pages" / "reference")
apidoc_excluded_paths = []
apidoc_separate_modules = True
apidoc_module_first = True
apidoc_toc_file = False
apidoc_template_dir = str(sourcedir / "_templates")
apidoc_extra_args = ["-P", f'--templatedir={apidoc_template_dir}']

# autodoc
autodoc_default_options = { 'autosummary': True }

# readme
readme_module_dir = str(basedir)
readme_output_dir = str(sourcedir / "pages" / "readme")

# sphinx
templates_path = ['_templates']
exclude_patterns = [ "static_pages" ]
root_doc = "pages/index"

# index
index_template_file = sourcedir / "_templates" / "index.rst_t"
index_pages_root = sourcedir / "pages"
index_sections = [
	"readme",
	"inputformat.md",
	"reference/endplay.rst"
]

# copy everything from 'pages' into 'build_pages'
copy_tree("static_pages", "pages", update=True)

# -- Options for HTML output -------------------------------------------------

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_css_files = [
	'css/split_params.css',
	'css/pretty_toc.css'
]
