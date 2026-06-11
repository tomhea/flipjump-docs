"""Sphinx configuration for fjdocs.tomhe.app.

M4: adds the `fj_stl_extract` extension which parses every .fj file
under vendor/flip-jump/flipjump/stl/ and renders per-file + per-macro
Markdown pages into stl/_generated/ on every build.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Put our extension package on sys.path so `extensions = ["fj_stl_extract"]`
# can find it. The package lives outside source/ to keep the Sphinx
# source tree clean.
_EXT_DIR = (Path(__file__).resolve().parent.parent / "_ext")
if str(_EXT_DIR) not in sys.path:
    sys.path.insert(0, str(_EXT_DIR))

project = "FlipJump Docs"
author = "Tom Herman"
copyright = "2026, Tom Herman"  # noqa: A001 — shadows Sphinx config slot
release = "1.1"

extensions = [
    "myst_parser",
    "sphinx_design",
    "sphinx_sitemap",
    "notfound.extension",
    "fj_stl_extract",
    "seo",
]

# SEO meta-tag + structured-data injection.
#
# `seo` is our own Sphinx extension (docs/_ext/seo) that hooks
# html-page-context and emits, on every page:
#   - <meta name="description"> (per-page, with manual overrides for the
#     top-level pages and auto-extraction from the first paragraph
#     elsewhere — see DEFAULT_PAGE_DESCRIPTIONS in the extension).
#   - <meta name="keywords"> (legacy, Google-ignored, kept for smaller
#     search engines).
#   - <meta name="robots" content="index, follow, max-image-preview:large">
#   - The full Open Graph and Twitter Card set (title, description, url,
#     image, type, site_name) so previews on Slack/Discord/Twitter/etc.
#     render with the FlipJump branding rather than a bare URL.
# And on the index page only:
#   - A JSON-LD WebSite schema with a SearchAction (enables a Google
#     sitelinks search box) and an alternateName list that maps the
#     site to "FlipJump Documentation", "FlipJump Docs", and "fjdocs".
#   - A JSON-LD SoftwareApplication schema describing FlipJump itself
#     (the language) so "FlipJump" / "FlipJump documentation" queries
#     can resolve us as the canonical reference for the language entity.
#
# Any of these defaults can be overridden by setting the matching
# `seo_*` config value below.
seo_site_name = "FlipJump Docs"
seo_site_description = (
    "Official FlipJump documentation — the one-instruction esoteric "
    "language. Standard library reference, language guide, cookbook, "
    "runnable examples, and the browser-based IDE."
)
seo_site_url = "https://fjdocs.tomhe.app/"
seo_og_image = "/og-image.png"
seo_twitter_handle = ""  # set to "tomhea" or similar to emit twitter:site/creator

# Algolia DocSearch integration. Currently using Sphinx's built-in
# client-side search; flipping `algolia_enabled = True` here (after
# applying to https://docsearch.algolia.com/apply) and filling in the
# three credential values will hand search off to Algolia DocSearch,
# which gives instant fuzzy results across the whole site.
#
# Application status: pending. Once approved Algolia provides:
#   appId, apiKey, indexName
# Filling them in and setting algolia_enabled = True wires the
# search box (via `_extra/algolia.js` and the layout override below).
algolia_enabled = False
algolia_app_id = ""
algolia_api_key = ""
algolia_index_name = "flipjump-docs"

# sphinx-sitemap needs the canonical URL to write absolute links.
html_baseurl = "https://fjdocs.tomhe.app/"
# Single-language, single-version site — strip the default `{lang}/{version}/`
# prefix that sphinx-sitemap inserts for multi-translation projects.
sitemap_url_scheme = "{link}"

# sphinx-notfound-page: serve a friendly 404 with site nav. We supply
# our own 404.md so the page has personality instead of just an
# auto-generated "not found" line. (`notfound_pagename` tells the
# extension to use our hand-written 404.md as the body source.)
notfound_urls_prefix = "/"
notfound_pagename = "404"

# Path resolution: from docs/source/conf.py, the flip-jump submodule
# sits at ../../vendor/flip-jump/flipjump/stl. This is the default in
# the extension; declared here for visibility.
fj_stl_root = "../../vendor/flip-jump/flipjump/stl"
fj_stl_output = "stl"

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "attrs_inline",
    "attrs_block",
    "fieldlist",
]
myst_heading_anchors = 3

source_suffix = {
    ".md": "markdown",
    ".rst": "restructuredtext",
}

exclude_patterns: list[str] = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
]

html_theme = "furo"
html_title = "FlipJump Docs"
# `_static/` holds custom CSS and theme assets that Sphinx serves under
# /_static/. `_extra/` ships verbatim to the deploy root (sibling of
# /index.html) — used for robots.txt and the favicons.
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_extra_path = ["_extra"]

html_favicon = "_extra/favicon.ico"

# Furo theme options: a permanent "Try the IDE" button in the top
# right of every page, plus an Edit-on-GitHub link.
html_theme_options = {
    "source_repository": "https://github.com/tomhea/flipjump-docs/",
    "source_branch": "main",
    "source_directory": "docs/source/",
    "top_of_page_buttons": ["view", "edit"],
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/tomhea/flipjump",
            "html": "",
            "class": "fa-brands fa-github",
        },
    ],
    "announcement": (
        '🚀 Try FlipJump in your browser: '
        '<a href="https://fj.tomhe.app" style="color: #e8c47a; '
        'text-decoration: underline; font-weight: bold;">'
        'fj.tomhe.app</a>'
    ),
}

# Apple-touch-icon + 32x32 PNG favicon: Furo refuses to be extended
# via layout.html, and `html_favicon` covers only the .ico. The
# fj_stl_extract Sphinx extension wires the additional <link> tags
# via the `html-page-context` event — see sphinx_ext.py.

# Custom Pygments style matching the FlipJump IDE's `fj-dark` theme so
# code blocks here look identical to code in the editor at fj.tomhe.app.
# The module-path string lets Sphinx import it as a custom style class.
pygments_style = "fj_stl_extract.pygments_style.FlipJumpDarkStyle"
pygments_dark_style = "fj_stl_extract.pygments_style.FlipJumpDarkStyle"

# Permanent "Try the IDE" link will move into html_theme_options in M8;
# left out at M1 so empty-scaffold Furo defaults render cleanly.
