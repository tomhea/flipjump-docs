"""Sphinx extension: SEO meta tags + Open Graph + Twitter Card + JSON-LD.

Injects, on every HTML page:

  - `<meta name="description">` — per-page, with manual overrides for the
    top-level pages and auto-extraction from the doctree's first paragraph
    for everything else.
  - `<meta name="keywords">` — kept for legacy crawlers; Google ignores it
    but a few smaller search engines still rank against it.
  - `<meta name="robots" content="index, follow, max-image-preview:large">`
    — explicit allow + large image preview consent.
  - Open Graph tags (`og:title`, `og:description`, `og:url`, `og:image`,
    `og:type`, `og:site_name`, `og:image:alt`) for Facebook / Slack /
    Discord / LinkedIn / etc. previews.
  - Twitter Card tags (`twitter:card=summary_large_image`, plus title /
    description / image, and optional `twitter:site`/`twitter:creator`).

Injects, on the index page only:

  - One JSON-LD `WebSite` schema with a `SearchAction` so Google can
    surface a sitelinks search box.
  - One JSON-LD `SoftwareApplication` schema describing FlipJump itself
    (the language), pointing at the PyPI download URL.

Configuration (set in `conf.py`):

    seo_site_name           default "FlipJump Docs"
    seo_site_description    default: a generic landing description
    seo_site_url            FALLBACK only — used if `html_baseurl` is
                            not set. With `html_baseurl` set in conf.py
                            (which is the norm for sphinx-sitemap to
                            work) this value is unused.
    seo_og_image            default "/og-image.png" (relative to site root)
    seo_twitter_handle      default "" (no twitter:site/creator emitted)
    seo_page_descriptions   default {}; map of pagename → description
                            override (use for pages where the first
                            paragraph isn't a good search snippet).
"""

from __future__ import annotations

import html
import json
import re
from typing import Any
from urllib.parse import urljoin

__all__ = ["setup"]


# Built-in per-page descriptions for the top-level pages. These are the
# pages most likely to be a Google landing page for keywords like
# "FlipJump Docs", "FlipJump STL", "FlipJump tutorial". A user override
# in `seo_page_descriptions` wins over these.
DEFAULT_PAGE_DESCRIPTIONS = {
    "index": (
        "Official FlipJump documentation: the one-instruction esoteric "
        "language, its standard library, language guide, cookbook, and "
        "browser-based IDE."
    ),
    "stl/index": (
        "FlipJump Standard Library (STL) reference: every macro in the "
        "bit, hex, hex.pointers, and stl namespaces — signatures, "
        "complexities, dependencies, and source links."
    ),
    "getting-started/index": (
        "Getting started with FlipJump: install the fj CLI, write your "
        "first program, learn the program skeleton, and run hello-world."
    ),
    "language/index": (
        "FlipJump language reference: the a;b instruction, expression "
        "syntax, macros, namespaces, directives, I/O, and complexity "
        "notation."
    ),
    "cookbook/index": (
        "FlipJump cookbook — short, runnable recipes for printing, "
        "conditionals, loops, swap, add, function calls, and decimal "
        "output."
    ),
    "examples/index": (
        "Annotated FlipJump example programs — hello world, prime sieve, "
        "calculator, quine, all runnable from the fj CLI."
    ),
    "reference/index": (
        "FlipJump reference material: glossary, how the STL works, "
        "complexity notation, and the underlying machine model."
    ),
    "tools/index": (
        "Companion tools for FlipJump — the browser IDE, c2fj (C "
        "compiler), bf2fj (Brainfuck compiler), the Claude Code skill, "
        "and the upstream language repo."
    ),
    "tools/ide": (
        "FlipJump IDE at fj.tomhe.app — browser-based editor, compiler, "
        "and runtime. Write FlipJump, hit Run, see output — no install."
    ),
    "tools/c2fj": (
        "c2fj — the C-to-FlipJump compiler. Pipeline: C → RISC-V → "
        "FlipJump. Install with pip install c2fj."
    ),
    "tools/bf2fj": (
        "bf2fj — the Brainfuck-to-FlipJump compiler with four "
        "optimisation passes. Install with pip install bf2fj."
    ),
    "tools/claude-skill": (
        "FlipJump Claude Skill — a Claude Code / Agent SDK skill bundle "
        "that teaches Claude to write, debug, and verify FlipJump "
        "programs end-to-end against the fj CLI."
    ),
    "tools/flip-jump": (
        "tomhea/flip-jump — the upstream repository: language "
        "implementation, standard library source, example programs, "
        "tests, and the GitHub wiki."
    ),
    "tools/esolangs": (
        "esolangs.org/FlipJump — the canonical external reference for "
        "FlipJump's design, computational classification, and "
        "related single-instruction languages."
    ),
    "404": (
        "Page not found — the FlipJump Docs site. Use the navigation or "
        "search to find the macro, page, or tutorial you were looking for."
    ),
}


# Universal keyword string. Google has ignored <meta name=keywords> for
# over a decade but some smaller engines (DuckDuckGo's primary index
# crawler, several enterprise search appliances) still factor it in.
KEYWORDS = (
    "FlipJump, FlipJump documentation, FlipJump docs, FlipJump STL, "
    "FlipJump standard library, FlipJump tutorial, FlipJump reference, "
    "esoteric language, one-instruction language, OISC, "
    "flip jump language, fj language"
)


def _first_paragraph(doctree: Any) -> str:
    """Extract the first non-banner paragraph from a docutils doctree.

    Skips paragraphs that look like ASCII banners or section dividers —
    e.g. STL file docstrings begin with `---------- Arithmetical Macros`
    on a single line, which is a heading-by-convention in the source but
    just punctuation noise in a meta-description.
    """
    if doctree is None:
        return ""
    try:
        from docutils import nodes  # type: ignore[import-not-found]

        # Punctuation chars that count as "banner-y" (ASCII dashes,
        # equals, asterisk, hash, underscore, tilde, plus, backtick, pipe,
        # slashes, angle brackets, PLUS the Unicode em-dash and en-dash
        # which MyST's smart-dashes filter substitutes for `---` / `--`).
        PUNCT = r"[\s\-=*#_~`+|/\\<>—–]"

        for para in doctree.traverse(nodes.paragraph):
            text = para.astext().strip()
            if not text:
                continue
            # Skip paragraphs that are mostly punctuation (banner dashes,
            # rule lines, hash-row separators).
            non_punct = re.sub(PUNCT, "", text)
            if not non_punct or len(non_punct) < 20:
                continue
            # FJ source-file banners look like "---------- Arithmetical
            # Macros" — a long punctuation run, then a short caption.
            # MyST turns long dash runs into em-dashes, so we have to
            # strip either form.
            text = re.sub(rf"^{PUNCT}{{3,}}\s*", "", text)
            if text:
                return text
    except Exception:  # pragma: no cover — Sphinx provides docutils
        pass
    return ""


def _truncate(text: str, max_len: int = 160) -> str:
    """Whitespace-normalise and truncate to max_len chars, ending on a word.

    160 is Google's desktop snippet limit (mobile cuts at ~130). We aim
    to land descriptions under this so the visible Google snippet never
    shows our own trailing `…` — the built-in descriptions for the
    landing pages are all hand-shortened below 160.
    """
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_len:
        return text
    cut = text[: max_len - 1].rsplit(" ", 1)[0]
    return cut + "…"


def _page_description(app: Any, pagename: str, doctree: Any) -> str:
    overrides = app.config.seo_page_descriptions or {}
    if pagename in overrides:
        return _truncate(_strip_tags(overrides[pagename]))
    if pagename in DEFAULT_PAGE_DESCRIPTIONS:
        return _truncate(_strip_tags(DEFAULT_PAGE_DESCRIPTIONS[pagename]))
    paragraph = _first_paragraph(doctree)
    if paragraph:
        # STL macro paragraphs sometimes contain literal `<br />` from
        # the FJ doc-comment continuation marker — strip those too.
        return _truncate(_strip_tags(paragraph))
    return _truncate(app.config.seo_site_description)


def _page_url(app: Any, pagename: str) -> str:
    base = app.config.html_baseurl or app.config.seo_site_url or ""
    if not base.endswith("/"):
        base += "/"
    return urljoin(base, pagename + ".html")


def _absolute_image(app: Any, image: str) -> str:
    if image.startswith(("http://", "https://")):
        return image
    base = (app.config.html_baseurl or app.config.seo_site_url or "").rstrip("/")
    if image.startswith("/"):
        return base + image
    return base + "/" + image


_TAG_RE = re.compile(r"<[^>]+>")


def _strip_tags(s: str) -> str:
    """Drop HTML tags from a title string. Sphinx puts <code> in titles
    when the page heading contains inline code (e.g. `# `bit/math.fj``)."""
    return _TAG_RE.sub("", s).strip()


def _page_title(pagename: str, context: dict, app: Any) -> str:
    """The full page title used for og:title / twitter:title.

    On the index page we just return the site name — the page H1 is
    "FlipJump" but the OG card should read "FlipJump Docs" to match the
    site identity, not "FlipJump — FlipJump Docs". On every other page
    we return "Page Title — Site Name", with any inline HTML in the
    title stripped so a heading like `bit/math.fj` (wrapped in <code>
    by docutils) becomes plain text in the OG card.
    """
    site_name = app.config.seo_site_name
    if pagename in ("index", ""):
        return site_name
    page_title = _strip_tags(context.get("title") or context.get("shorttitle") or "")
    if not page_title or page_title == site_name:
        return site_name
    return f"{page_title} — {site_name}"


def _build_meta_block(
    app: Any, pagename: str, context: dict, doctree: Any
) -> str:
    description = _page_description(app, pagename, doctree)
    page_url = _page_url(app, pagename)
    page_title = _page_title(pagename, context, app)
    site_name = app.config.seo_site_name
    og_image = _absolute_image(app, app.config.seo_og_image)
    twitter_handle = (app.config.seo_twitter_handle or "").lstrip("@")

    is_index = pagename in ("index", "")
    og_type = "website" if is_index else "article"

    def esc(s: str) -> str:
        return html.escape(s, quote=True)

    parts = [
        f'<meta name="description" content="{esc(description)}">',
        f'<meta name="keywords" content="{esc(KEYWORDS)}">',
        '<meta name="robots" content="index, follow, max-image-preview:large">',
        f'<meta property="og:type" content="{og_type}">',
        f'<meta property="og:site_name" content="{esc(site_name)}">',
        f'<meta property="og:title" content="{esc(page_title)}">',
        f'<meta property="og:description" content="{esc(description)}">',
        f'<meta property="og:url" content="{esc(page_url)}">',
        f'<meta property="og:image" content="{esc(og_image)}">',
        f'<meta property="og:image:alt" content="{esc(site_name)}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{esc(page_title)}">',
        f'<meta name="twitter:description" content="{esc(description)}">',
        f'<meta name="twitter:image" content="{esc(og_image)}">',
    ]
    if twitter_handle:
        parts.append(f'<meta name="twitter:site" content="@{esc(twitter_handle)}">')
        parts.append(f'<meta name="twitter:creator" content="@{esc(twitter_handle)}">')

    # Structured data: emit on the landing page so Google can resolve
    # the "official site for X" / "X documentation" entity and surface a
    # sitelinks search box.
    if is_index:
        site_url = (app.config.html_baseurl or app.config.seo_site_url or "").rstrip("/") + "/"
        version = getattr(app.config, "release", "")
        website_jsonld = {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": site_name,
            "alternateName": [
                "FlipJump Documentation",
                "FlipJump Docs",
                "fjdocs",
                "fjdocs.tomhe.app",
            ],
            "url": site_url,
            "description": description,
            "inLanguage": "en",
            "publisher": {
                "@type": "Person",
                "name": "Tom Herman",
                "url": "https://github.com/tomhea",
            },
            "potentialAction": {
                "@type": "SearchAction",
                "target": {
                    "@type": "EntryPoint",
                    "urlTemplate": site_url + "search.html?q={search_term_string}",
                },
                "query-input": "required name=search_term_string",
            },
        }
        software_jsonld: dict[str, Any] = {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": "FlipJump",
            "alternateName": ["flip-jump", "FJ language"],
            "description": (
                "FlipJump is a one-instruction esoteric programming language. "
                "The only instruction is a;b: flip the bit at address a, then "
                "jump to address b. A substantial standard library implements "
                "variables, arithmetic, I/O, pointers, and a stack on top."
            ),
            "applicationCategory": "DeveloperApplication",
            "operatingSystem": "Cross-platform",
            "url": "https://github.com/tomhea/flip-jump",
            "downloadUrl": "https://pypi.org/project/flipjump/",
            "author": {
                "@type": "Person",
                "name": "Tom Herman",
                "url": "https://github.com/tomhea",
            },
            "offers": {
                "@type": "Offer",
                "price": "0",
                "priceCurrency": "USD",
            },
        }
        if version:
            software_jsonld["softwareVersion"] = version
        parts.append(
            '<script type="application/ld+json">'
            + json.dumps(website_jsonld, separators=(",", ":"))
            + "</script>"
        )
        parts.append(
            '<script type="application/ld+json">'
            + json.dumps(software_jsonld, separators=(",", ":"))
            + "</script>"
        )

    return "\n".join(parts)


def _on_html_page_context(
    app: Any, pagename: str, templatename: str, context: dict, doctree: Any
) -> None:
    block = _build_meta_block(app, pagename, context, doctree)
    existing = context.get("metatags", "")
    context["metatags"] = (existing + "\n" + block) if existing else block


def setup(app: Any) -> dict[str, Any]:
    app.add_config_value("seo_site_name", "FlipJump Docs", "env")
    app.add_config_value(
        "seo_site_description",
        (
            "Official FlipJump documentation — the one-instruction esoteric "
            "language. Standard library reference, language guide, cookbook, "
            "runnable examples, and the browser-based IDE."
        ),
        "env",
    )
    app.add_config_value("seo_site_url", "https://fjdocs.tomhe.app/", "env")
    app.add_config_value("seo_og_image", "/og-image.png", "env")
    app.add_config_value("seo_twitter_handle", "", "env")
    app.add_config_value("seo_page_descriptions", {}, "env")
    app.connect("html-page-context", _on_html_page_context)
    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
