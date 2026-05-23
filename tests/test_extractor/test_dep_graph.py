"""Dependency-graph contract tests."""

from __future__ import annotations

from fj_stl_extract.dep_graph import build_dep_graph, macro_key
from fj_stl_extract.parser import parse


def _graph(src: str):
    file = parse(src)
    return file, build_dep_graph(file.macros)


# ---------- basic edges ----------

def test_absolute_call_creates_edge():
    src = """\
ns stl { def helper {} }
ns bit { def caller { stl.helper } }
"""
    file, g = _graph(src)
    [helper] = [m for m in file.macros if m.name == "helper"]
    [caller] = [m for m in file.macros if m.name == "caller"]
    assert macro_key(helper) in g.depends_on[macro_key(caller)]
    assert macro_key(caller) in g.used_by[macro_key(helper)]


def test_leading_dot_resolves_to_current_namespace():
    src = """\
ns hex {
    def helper {}
    def caller { .helper }
}
"""
    file, g = _graph(src)
    [helper] = [m for m in file.macros if m.name == "helper"]
    [caller] = [m for m in file.macros if m.name == "caller"]
    assert macro_key(helper) in g.depends_on[macro_key(caller)]


def test_double_dot_resolves_to_parent_namespace():
    src = """\
ns hex {
    def helper {}
    ns add {
        def caller { ..helper }
    }
}
"""
    file, g = _graph(src)
    [helper] = [m for m in file.macros if m.name == "helper"]
    [caller] = [m for m in file.macros if m.name == "caller"]
    assert macro_key(helper) in g.depends_on[macro_key(caller)]


def test_bare_word_resolves_to_current_namespace_first():
    src = """\
def helper {}
ns hex {
    def helper {}
    def caller { helper }
}
"""
    file, g = _graph(src)
    callers = [m for m in file.macros if m.name == "caller"]
    helpers = [m for m in file.macros if m.name == "helper" and m.namespace_path == ("hex",)]
    [caller] = callers
    [hex_helper] = helpers
    # Caller resolves to hex.helper, not the global helper.
    assert macro_key(hex_helper) in g.depends_on[macro_key(caller)]


# ---------- arity overloading ----------

def test_call_with_matching_arity_links_only_that_overload():
    src = """\
ns stl {
    def m { x }
    def m a, b { x }
    def m a, b, c { x }
    def caller { stl.m 1, 2 }
}
"""
    file, g = _graph(src)
    arity2 = [m for m in file.macros if m.name == "m" and m.arity == 2][0]
    arity0 = [m for m in file.macros if m.name == "m" and m.arity == 0][0]
    [caller] = [m for m in file.macros if m.name == "caller"]
    assert macro_key(arity2) in g.depends_on[macro_key(caller)]
    assert macro_key(arity0) not in g.depends_on[macro_key(caller)]


def test_call_with_no_matching_arity_links_all_overloads():
    src = """\
ns stl {
    def m a, b { x }
    def m a, b, c { x }
    def caller { stl.m 1, 2, 3, 4 }
}
"""
    file, g = _graph(src)
    callees = {macro_key(m) for m in file.macros if m.name == "m"}
    [caller] = [m for m in file.macros if m.name == "caller"]
    # Neither overload matches arity 4, so both get linked.
    assert g.depends_on[macro_key(caller)] == callees


# ---------- statement-start detection ----------

def test_only_statement_start_idents_count_as_calls():
    src = """\
ns stl { def target {} }
ns stl { def caller { stl.target stl.target } }
"""
    # The second `stl.target` appears as an ARG, not a call. So we link
    # `caller -> target` exactly once (not twice).
    file, g = _graph(src)
    [target] = [m for m in file.macros if m.name == "target"]
    [caller] = [m for m in file.macros if m.name == "caller"]
    assert g.depends_on[macro_key(caller)] == {macro_key(target)}


def test_semi_resets_statement_start():
    src = """\
ns stl {
    def a {}
    def b {}
    def caller { stl.a ; stl.b }
}
"""
    file, g = _graph(src)
    [a] = [m for m in file.macros if m.name == "a"]
    [b] = [m for m in file.macros if m.name == "b"]
    [caller] = [m for m in file.macros if m.name == "caller"]
    assert g.depends_on[macro_key(caller)] == {macro_key(a), macro_key(b)}


# ---------- unresolved (loop vars, runtime labels) ----------

def test_unknown_callee_recorded_in_unresolved():
    src = """\
ns stl { def caller { does.not.exist 1, 2 } }
"""
    file, g = _graph(src)
    [caller] = [m for m in file.macros if m.name == "caller"]
    assert "does.not.exist" in g.unresolved[macro_key(caller)]
    assert g.depends_on[macro_key(caller)] == set()


def test_caller_own_params_locals_labels_are_not_unresolved():
    """Param/local/exported-label/required-label names used at body
    statement-start must NOT pollute the `unresolved` set — they are
    local references, not external macro calls. (CR-ist finding on M3.)

    Also verifies the dot-strip: a `< .ret` clause matches both `.ret`
    AND bare `ret` in the body (the user might use either form).
    """
    src = """\
ns stl { def target {} }
ns stl {
    def caller dst, src @ end < .ret, ..tables.foo > IO {
        stl.target
        dst end .ret ret src IO ..tables.foo
        tables.foo
    }
}
"""
    file, g = _graph(src)
    [caller] = [m for m in file.macros if m.name == "caller"]
    unresolved = g.unresolved.get(macro_key(caller), set())
    expected_filtered = (
        "dst", "src", "end", "IO",
        ".ret", "ret",
        "..tables.foo", "tables.foo",
    )
    for bound in expected_filtered:
        assert bound not in unresolved, (
            f"{bound!r} is a caller-bound name (or its dot-stripped form) "
            f"and should not appear in unresolved, got: {unresolved}"
        )


# ---------- realistic STL fragment ----------

def test_runlib_startup_dependencies():
    src = """\
ns stl {
    def startup code_start > IO { ;code_start IO: ;0 }
    def startup @ code_start { stl.startup code_start }
}
"""
    file, g = _graph(src)
    [base] = [m for m in file.macros if m.name == "startup" and m.arity == 1]
    [wrapper] = [m for m in file.macros if m.name == "startup" and m.arity == 0]
    # Wrapper calls base/arity-1.
    deps = g.depends_on[macro_key(wrapper)]
    assert macro_key(base) in deps
    assert macro_key(wrapper) in g.used_by[macro_key(base)]
