import os
import sys
sys.path.insert(0, os.path.abspath("../.."))  # so it can import my_ping, utils

project = "Ping and Traceroute"
author = "Abdul Aleem Shaik Gadda"
release = "1.0"

extensions = [
    "sphinx.ext.autodoc",       # pulls docs from docstrings
]

# Keep functions in the order they appear in the file
autodoc_member_order = "bysource"

# Cleaner, more consistent PDF
latex_elements = {
    "papersize": "a4paper",      # or "letterpaper"
    "pointsize": "11pt",
    "extraclassoptions": "openany,oneside",  # no blank pages between chapters
}
import inspect

def add_source(app, what, name, obj, options, lines):
    if app.builder.name != "latex":   # PDF only; HTML keeps [source] links
        return
    if what not in ("function", "method"):
        return
    try:
        src = inspect.getsource(obj)
    except (TypeError, OSError):
        return
    lines += ["", "*Source code:*", "", ".. code-block:: python", ""]
    lines += ["   " + line for line in src.splitlines()]

def setup(app):
    app.connect("autodoc-process-docstring", add_source)