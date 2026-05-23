"""End-to-end tests against the real `vendor/flip-jump/flipjump/stl/`.

These tests pin the extractor against upstream so the weekly
`submodule-bump.yml` PR will surface upstream STL changes as test
failures we can investigate before merging the bump.

Tests are skipped if the submodule isn't initialised.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from fj_stl_extract.dep_graph import macro_key
from fj_stl_extract.pipeline import extract_stl, to_json_dict

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
STL_ROOT = REPO_ROOT / "vendor" / "flip-jump" / "flipjump" / "stl"


@pytest.fixture(scope="module")
def index():
    if not (STL_ROOT / "conf.json").is_file():
        pytest.skip("flip-jump submodule not initialised")
    return extract_stl(STL_ROOT)


# ---------- shape sanity ----------

def test_every_file_in_conf_json_was_extracted(index):
    import json
    expected = json.loads((STL_ROOT / "conf.json").read_text())["all"]
    actual = [f.rel_path for f in index.files]
    assert actual == expected


def test_top_level_constants_dw_and_dbit_are_recognised(index):
    runlib = next(f for f in index.files if f.rel_path == "runlib")
    names = {c.name for c in runlib.file_node.constants}
    assert {"dw", "dbit"} <= names


def test_at_least_one_macro_per_file(index):
    for f in index.files:
        assert f.file_node.macros, f"{f.rel_path} has no macros"


# ---------- known macros land in the index ----------

@pytest.mark.parametrize("expected", [
    "stl.startup",
    "stl.startup_and_init_all",
    "stl.loop",
    "stl.fj",
    "stl.wflip_macro",
    "bit.add",
    "hex.add",
    "hex.div",
    "hex.pointers.ptr_init",
])
def test_known_macros_present(index, expected: str):
    fq_names = {m.fq_name for m in index.all_macros}
    assert expected in fq_names, f"{expected} not found in STL extraction"


# ---------- arity overloads are distinct ----------

def test_stl_startup_has_arity_0_and_arity_1(index):
    startups = [m for m in index.all_macros if m.fq_name == "stl.startup"]
    arities = sorted(m.arity for m in startups)
    assert arities == [0, 1]


def test_stl_wflip_macro_has_2_and_3_arg_overloads(index):
    wflips = [m for m in index.all_macros if m.fq_name == "stl.wflip_macro"]
    arities = sorted(m.arity for m in wflips)
    assert arities == [2, 3]


# ---------- doc extraction ----------

def test_runlib_startup_has_io_output_param_doc(index):
    runlib = next(f for f in index.files if f.rel_path == "runlib")
    base = next(m for m in runlib.file_node.macros
                if m.name == "startup" and m.arity == 1)
    doc = runlib.docs[id(base)]
    assert "IO" in doc.output_params


def test_some_macros_have_time_and_space_complexity(index):
    with_time = [m for m in index.all_macros
                 if any(f.docs[id(m)].time_complexity
                        for f in index.files if id(m) in f.docs)]
    # At least the bit/math and hex/math macros should be annotated.
    assert with_time, "expected at least one macro with time complexity"


def test_hex_add_has_requires_init_tag(index):
    hex_math = next(f for f in index.files if f.rel_path == "hex/math")
    add = next(m for m in hex_math.file_node.macros
               if m.name == "add" and m.arity == 2)
    doc = hex_math.docs[id(add)]
    assert any("hex.add.init" in r or "hex.init" in r for r in doc.requires)


# ---------- dependency graph ----------

def test_dep_graph_has_edges(index):
    g = index.dep_graph
    assert g is not None
    assert sum(len(s) for s in g.depends_on.values()) > 0


def test_stl_startup_called_by_stl_startup_and_init_pointers(index):
    g = index.dep_graph
    init_p = next(m for m in index.all_macros
                  if m.fq_name == "stl.startup_and_init_pointers"
                  and m.arity == 1)
    callers = g.depends_on.get(macro_key(init_p), set())
    # Should call stl.startup/1 (overloaded with arity 1).
    assert any(c.startswith("stl.startup/") for c in callers)


# ---------- JSON serialisation round-trip ----------

def test_to_json_dict_serialises(index):
    import json
    out = to_json_dict(index)
    text = json.dumps(out)
    assert len(text) > 10_000  # the STL is non-trivial
    assert '"stl.startup"' in text or '"stl.startup_and_init_all"' in text


# ---------- regression-guard: no crashes on the full corpus ----------

def test_extractor_does_not_record_macros_with_empty_names(index):
    for m in index.all_macros:
        assert m.name, f"empty macro name in {m.namespace_path}"


def test_extractor_attaches_doc_to_every_macro_object(index):
    for f in index.files:
        for m in f.file_node.macros:
            assert id(m) in f.docs
