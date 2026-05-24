# Algolia DocSearch setup

Pending application. When the Algolia team approves the docs site at <https://docsearch.algolia.com/apply>, they will send three credentials:

- `appId`
- `apiKey` (search-only, safe to ship in client-side JS)
- `indexName`

To wire them up:

1. Edit `docs/source/conf.py`:
   - Set `algolia_enabled = True`
   - Fill in `algolia_app_id`, `algolia_api_key`, `algolia_index_name`
2. The build will then inject the DocSearch CSS + JS bundle via the
   `html-page-context` handler in `fj_stl_extract.sphinx_ext` (see
   the `_inject_algolia_search` function — to be added when
   credentials arrive).
3. Furo's built-in search box gets replaced by the Algolia widget.

Until the credentials are in place the site uses Sphinx's built-in
client-side searchindex.js, which works fine for the current ~500
pages but gets sluggish past ~1000.
