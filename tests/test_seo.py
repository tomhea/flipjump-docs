"""SEO extension tests — verify meta description, Open Graph, Twitter
Card, and JSON-LD structured data render correctly across the site.

The test builds the site once (cached in a tmp dir) and then asserts
against the produced HTML. Each individual assertion is its own test
function so the failure surface is narrow.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_SOURCE = REPO_ROOT / "docs" / "source"


@pytest.fixture(scope="module")
def built_site(tmp_path_factory):
    """Build the docs site once per test module and return the html dir."""
    try:
        import sphinx  # noqa: F401
    except ImportError:
        pytest.skip("sphinx not installed in this interpreter")

    out_dir = tmp_path_factory.mktemp("html")
    result = subprocess.run(
        [sys.executable, "-m", "sphinx", "-W", "-b", "html",
         str(DOCS_SOURCE), str(out_dir)],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    assert result.returncode == 0, (
        f"sphinx -m failed with exit code {result.returncode}\n"
        f"STDOUT:\n{result.stdout[-2000:]}\n"
        f"STDERR:\n{result.stderr[-2000:]}"
    )
    return out_dir


# ---------- JSON-LD <script> safety (no build needed) ----------

def test_seo_json_ld_escapes_html_for_script_context():
    """The SEO module emits JSON-LD inside inline `<script>` blocks. The
    serialiser must `\\uXXXX`-escape HTML-significant characters so a
    `</script>` can never break out of the block, mirroring the
    fj_stl_extract renderer's `</script>`-safe serialisation."""
    import json

    from seo import _json_ld

    out = _json_ld({"description": "</script><svg onload=alert(1)>&"})
    assert "<" not in out
    assert ">" not in out
    assert "&" not in out
    assert json.loads(out)["description"] == "</script><svg onload=alert(1)>&"


def _read(html_dir: Path, page: str) -> str:
    p = html_dir / page
    assert p.is_file(), f"{p} not built"
    return p.read_text(encoding="utf-8")


def _meta(html: str, name: str = "", prop: str = "") -> str | None:
    """Extract the `content` of <meta name=...> or <meta property=...>."""
    if name:
        pat = rf'<meta name="{re.escape(name)}" content="([^"]*)"'
    else:
        pat = rf'<meta property="{re.escape(prop)}" content="([^"]*)"'
    m = re.search(pat, html)
    return m.group(1) if m else None


def test_index_has_description(built_site):
    html = _read(built_site, "index.html")
    desc = _meta(html, name="description")
    assert desc, "index.html missing <meta name=description>"
    assert "FlipJump documentation" in desc
    # Description should fit Google's snippet length budget.
    assert 50 <= len(desc) <= 160, f"description out of band: {len(desc)} chars"


def test_index_has_og_tags(built_site):
    html = _read(built_site, "index.html")
    assert _meta(html, prop="og:type") == "website"
    assert _meta(html, prop="og:site_name") == "FlipJump Docs"
    assert _meta(html, prop="og:title") == "FlipJump Docs"
    assert _meta(html, prop="og:url") == "https://fjdocs.tomhe.app/index.html"
    og_image = _meta(html, prop="og:image")
    assert og_image == "https://fjdocs.tomhe.app/og-image.png", (
        f"og:image must be an absolute URL pointing at the social card; got {og_image!r}"
    )


def test_index_has_twitter_card(built_site):
    html = _read(built_site, "index.html")
    assert _meta(html, name="twitter:card") == "summary_large_image"
    assert _meta(html, name="twitter:title") == "FlipJump Docs"
    assert _meta(html, name="twitter:image") == "https://fjdocs.tomhe.app/og-image.png"


def test_index_has_robots_allow(built_site):
    html = _read(built_site, "index.html")
    robots = _meta(html, name="robots")
    assert robots and "index" in robots and "follow" in robots


def test_index_has_jsonld(built_site):
    """Both WebSite (with SearchAction) and SoftwareApplication schemas."""
    import json

    html = _read(built_site, "index.html")
    blocks = re.findall(
        r'<script type="application/ld\+json">(.+?)</script>', html, re.DOTALL
    )
    parsed = [json.loads(b) for b in blocks]
    types = {p.get("@type") for p in parsed}
    assert "WebSite" in types, f"Missing WebSite JSON-LD; got {types}"
    assert "SoftwareApplication" in types, f"Missing SoftwareApplication JSON-LD; got {types}"
    website = next(p for p in parsed if p["@type"] == "WebSite")
    assert "FlipJump Documentation" in website.get("alternateName", [])
    assert website.get("potentialAction", {}).get("@type") == "SearchAction"


def test_stl_page_description_clean(built_site):
    """The auto-derived first-paragraph description must skip banner dashes
    and `<br />` HTML from STL file docstrings."""
    html = _read(built_site, "stl/bit/math.html")
    desc = _meta(html, name="description")
    assert desc, "stl/bit/math.html missing meta description"
    # The bit/math.fj source begins with `---------- Arithmetical Macros`.
    # MyST turns long dash runs into em-dashes — both forms must be stripped.
    assert not desc.startswith(("-", "—", "–")), (
        f"description starts with leftover banner punctuation: {desc!r}"
    )
    assert "Arithmetical" in desc


def test_macro_page_description_no_html(built_site):
    """Inline `<br />` from doc-comment continuations must not leak."""
    html = _read(built_site, "stl/bit/math/add--3.html")
    desc = _meta(html, name="description")
    assert desc and "<" not in desc and ">" not in desc, (
        f"description must not contain HTML tags; got {desc!r}"
    )


def test_macro_page_og_title_no_html(built_site):
    """og:title must be plain text — Sphinx wraps inline-code in
    page titles with <code>; the SEO extension must strip those."""
    html = _read(built_site, "stl/bit/math/add--3.html")
    t = _meta(html, prop="og:title")
    assert t and "<" not in t and ">" not in t, (
        f"og:title must be plain text; got {t!r}"
    )
    assert "bit.add" in t


def test_non_index_pages_have_no_extra_jsonld(built_site):
    """SEO extension only adds JSON-LD to the index page. Macro pages
    have their own TechArticle JSON-LD from the macro template, but no
    page should have a WebSite block."""
    import json

    for page in (
        "getting-started/index.html",
        "language/index.html",
        "cookbook/index.html",
        "tools/index.html",
        "stl/index.html",
    ):
        html = _read(built_site, page)
        blocks = re.findall(
            r'<script type="application/ld\+json">(.+?)</script>',
            html,
            re.DOTALL,
        )
        for b in blocks:
            d = json.loads(b)
            assert d.get("@type") != "WebSite", (
                f"{page} should not have a WebSite JSON-LD block "
                f"(those are landing-page-only)"
            )


def test_canonical_and_og_url_agree(built_site):
    """Each page's <link rel=canonical> and og:url must point to the
    same URL — Google penalises mismatches."""
    for page in ("index.html", "stl/index.html", "tools/claude-skill.html"):
        html = _read(built_site, page)
        m = re.search(r'<link rel="canonical" href="([^"]*)"', html)
        assert m, f"{page} missing canonical"
        canonical = m.group(1)
        og_url = _meta(html, prop="og:url")
        assert canonical == og_url, (
            f"{page}: canonical={canonical!r} but og:url={og_url!r}"
        )


def test_og_image_is_served(built_site):
    """The OG card must be in the built tree at /og-image.png so social
    crawlers can fetch it."""
    img = built_site / "og-image.png"
    assert img.is_file(), "og-image.png must be served from site root"
    # Size check: at least 10KB (a real card, not an empty placeholder).
    assert img.stat().st_size > 10_000, f"og-image.png suspiciously small: {img.stat().st_size}B"


def test_index_description_not_truncated(built_site):
    """The hardcoded index description must fit under the 160-char snippet
    budget so the rendered output doesn't carry our own trailing `…` —
    if Google ever cuts the snippet itself, that's separate, but our own
    truncation marker should never appear on a hand-written description."""
    html = _read(built_site, "index.html")
    desc = _meta(html, name="description")
    assert desc and not desc.endswith("…"), (
        f"description shouldn't end with our truncation marker; got {desc!r}"
    )


def test_truncate_boundary():
    """_truncate must leave a 160-char string alone and add `…` at 161+."""
    from seo import _truncate  # noqa: PLC0415

    # Exactly at the limit: no truncation.
    s_160 = "a " * 80  # 160 chars
    s_160 = s_160[:160]
    assert _truncate(s_160) == s_160.strip()

    # One past the limit: truncated with the ellipsis character (not "...").
    s_161 = "x" * 161
    out = _truncate(s_161)
    assert out.endswith("…"), f"expected ellipsis suffix, got {out!r}"
    assert "..." not in out, "must use Unicode ellipsis, not three dots"
    assert len(out) <= 160, f"truncated output must fit in 160 chars, got {len(out)}"


def test_page_description_manual_override(tmp_path):
    """`seo_page_descriptions` should override both the built-in dictionary
    and any auto-extracted first paragraph."""
    # Reach into the module — easier than spinning up a whole sphinx app.
    from types import SimpleNamespace

    from seo import _page_description  # noqa: PLC0415

    fake_app = SimpleNamespace(
        config=SimpleNamespace(
            seo_page_descriptions={"index": "custom landing description for SEO"},
            seo_site_description="fallback",
        )
    )
    out = _page_description(fake_app, "index", doctree=None)
    assert out == "custom landing description for SEO"


def test_jsonld_only_on_index(built_site):
    """The SEO extension's WebSite + SoftwareApplication blocks must
    appear exactly once each — only on the index page."""
    import json

    pages_to_scan = [
        "index.html",
        "stl/index.html",
        "stl/bit/math.html",
        "stl/bit/math/add--3.html",
        "getting-started/index.html",
        "tools/claude-skill.html",
    ]
    counts = {"WebSite": 0, "SoftwareApplication": 0}
    for page in pages_to_scan:
        html = _read(built_site, page)
        blocks = re.findall(
            r'<script type="application/ld\+json">(.+?)</script>',
            html,
            re.DOTALL,
        )
        for b in blocks:
            d = json.loads(b)
            t = d.get("@type")
            if t in counts:
                counts[t] += 1
    assert counts["WebSite"] == 1, f"WebSite JSON-LD count: {counts['WebSite']}"
    assert counts["SoftwareApplication"] == 1, (
        f"SoftwareApplication JSON-LD count: {counts['SoftwareApplication']}"
    )
