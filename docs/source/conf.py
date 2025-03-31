# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
import django

sys.path.insert(0, os.path.abspath("../../src"))
os.environ["DJANGO_SETTINGS_MODULE"] = "core.settings"
django.setup()


project = "whorl-server"
copyright = "2025, Will Wolff, Hemani Alaparthi, Chezka Quinola, Darius Googe"
author = "Will Wolff, Hemani Alaparthi, Chezka Quinola, Darius Googe"
release = "0.0.9"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx.ext.autodoc"]

templates_path = ["_templates"]
exclude_patterns = []

language = "python"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
html_theme_options = {
    "default_dark_mode": True,
    "dark_css_variables": {
        # Background colors
        "color-background-primary": "#202020",  # Main content background
        "color-background-secondary": "#202020",  # Sidebar background
        # Text colors
        "color-foreground-primary": "#ffffff",  # Main text color
        "color-foreground-secondary": "#e0b027",  # Secondary text color
        # Link colors
        "color-brand-primary": "#e2ad2b",  # Primary brand color
        "color-brand-content": "#e2ad2b",  # Link color
        "color-link": "#e2ad2b",  # Normal links
        "color-link-hover": "#CEAFF4",  # Hover state
        "color-link--visited": "#CEAFF4",  # Visited links
        # Sidebar colors
        "color-sidebar-link-text": "#e0b027",  # Sidebar link color
        "color-sidebar-link-text--top-level": "#e2ad2b",  # Top level sidebar links
        # API/Code colors
        "color-api-name": "#e2ad2b",  # Function names
        "color-api-pre-name": "#e2ad2b",  # Class/module names
        "color-highlight-on-target": "#56595d",
    },
}
