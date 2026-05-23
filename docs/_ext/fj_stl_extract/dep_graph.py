"""Build the macro dependency graph.

Each macro is keyed by `"<fq_name>/<arity>"` so arity overloads (e.g.
`stl.startup/0` vs `stl.startup/1`) are distinct nodes.

Dependency resolution rules for an identifier token at a body's
statement-start position (after `{`, NEWLINE, or `;`):

    `stl.foo` / `bit.foo` / `hex.foo` ... absolute path → look up directly.
    `.foo`                                              → current namespace + foo.
    `..foo`                                             → parent namespace + foo.
    bare `foo`                                          → current namespace first, then global fallback.

Arity is heuristically resolved when possible (we read the comma count
of the call's arg list, ignoring tokens inside nested parens/braces).
Where multiple overloads match the same name, all matching arities are
recorded as edges so the per-page "Used by" lists capture all callers.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from .parser import MacroNode
from .tokenizer import Token, TokenKind

__all__ = ["DepGraph", "build_dep_graph", "macro_key"]


def macro_key(macro: MacroNode) -> str:
    return f"{macro.fq_name}/{macro.arity}"


@dataclass
class DepGraph:
    depends_on: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    used_by: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    unresolved: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))


def build_dep_graph(macros: list[MacroNode]) -> DepGraph:
    # Index: fq_name (without arity) → list of macros sharing that name.
    by_fq: dict[str, list[MacroNode]] = defaultdict(list)
    for m in macros:
        by_fq[m.fq_name].append(m)

    graph = DepGraph()
    for caller in macros:
        caller_key = macro_key(caller)
        # A statement-start identifier that matches one of the caller's
        # own bound names (param, @-local, <-required-label, >-exported-
        # label) is a local reference, not a call. Pre-compute the set
        # so we skip them cheaply — otherwise `unresolved` fills up with
        # every parameter mention in every body.
        #
        # `requires_labels` come in dot-prefixed (e.g. ".ret", "..tables.x")
        # because that's how they're written in source. A body usage like
        # bare `ret` should also be treated as bound — strip the leading
        # dots when adding to the filter set.
        bound = (set(caller.params) | set(caller.locals_)
                 | set(caller.exports_labels)
                 | {label.lstrip(".") for label in caller.requires_labels}
                 | set(caller.requires_labels))
        for callee_name, call_arity in _scan_calls(caller.body_tokens):
            if callee_name in bound:
                continue
            resolved = _resolve(callee_name, caller, by_fq)
            if not resolved:
                graph.unresolved[caller_key].add(callee_name)
                continue
            # If an arity-matching overload exists, prefer just it. Else
            # link all overloads (the caller likely refers to "any" of
            # them — e.g. when wrapping a name in a helper macro).
            arity_matches = [m for m in resolved if m.arity == call_arity]
            targets = arity_matches if arity_matches else resolved
            for target in targets:
                tk = macro_key(target)
                graph.depends_on[caller_key].add(tk)
                graph.used_by[tk].add(caller_key)
    return graph


# ---------- internals ----------

def _scan_calls(body: list[Token]) -> list[tuple[str, int]]:
    """Return (callee_name, call_arity) pairs at statement-start positions.

    Call arity is the comma count in the call's arg expression at the
    SAME paren-depth as the call name, terminated by a SEMI or NEWLINE.
    If a call has no args it has arity 0.
    """
    calls: list[tuple[str, int]] = []
    at_stmt_start = True
    i = 0
    while i < len(body):
        t = body[i]
        if t.kind in (TokenKind.NEWLINE, TokenKind.SEMI):
            at_stmt_start = True
            i += 1
            continue
        if t.kind == TokenKind.COMMENT:
            i += 1
            continue
        if at_stmt_start and t.kind == TokenKind.IDENT:
            arity, consumed = _count_args(body, i + 1)
            calls.append((t.text, arity))
            i += 1 + consumed
            at_stmt_start = False
            continue
        at_stmt_start = False
        i += 1
    return calls


def _count_args(body: list[Token], start: int) -> tuple[int, int]:
    """Count comma-separated args until the next SEMI / NEWLINE at depth 0.
    Returns (arity, tokens_consumed).
    """
    depth = 0
    commas = 0
    saw_anything = False
    i = start
    while i < len(body):
        t = body[i]
        if depth == 0 and t.kind in (TokenKind.SEMI, TokenKind.NEWLINE):
            break
        if t.kind in (TokenKind.LPAREN, TokenKind.LBRACE, TokenKind.LBRACKET):
            depth += 1
            saw_anything = True
        elif t.kind in (TokenKind.RPAREN, TokenKind.RBRACE, TokenKind.RBRACKET):
            depth -= 1
        elif depth == 0 and t.kind == TokenKind.COMMA:
            commas += 1
            saw_anything = True
        elif t.kind not in (TokenKind.COMMENT, TokenKind.NEWLINE):
            saw_anything = True
        i += 1
    consumed = i - start
    if not saw_anything:
        return 0, consumed
    return commas + 1, consumed


def _resolve(callee: str, caller: MacroNode,
             by_fq: dict[str, list[MacroNode]]) -> list[MacroNode]:
    """Resolve `callee` against the macro registry. Returns 0+ matches."""
    candidates = _candidate_fq_names(callee, caller)
    for fq in candidates:
        if fq in by_fq:
            return by_fq[fq]
    return []


def _candidate_fq_names(callee: str, caller: MacroNode) -> list[str]:
    """Generate possible fully-qualified names to try in order."""
    # Leading-dot resolution (current ns / parent ns).
    if callee.startswith(".."):
        # `..foo.bar` → parent namespace prefix + foo.bar
        # parent = caller.namespace_path[:-1]
        parent = caller.namespace_path[:-1]
        suffix = callee.lstrip(".")
        if parent:
            return [".".join(parent) + "." + suffix]
        return [suffix]
    if callee.startswith("."):
        # `.foo.bar` → current namespace prefix + foo.bar
        suffix = callee.lstrip(".")
        if caller.namespace_path:
            return [".".join(caller.namespace_path) + "." + suffix]
        return [suffix]

    # Already absolute (contains a dot, not leading): use as-is.
    if "." in callee:
        return [callee]

    # Bare word: try current namespace, then current's ancestors, then global.
    out: list[str] = []
    ns = list(caller.namespace_path)
    while ns:
        out.append(".".join(ns) + "." + callee)
        ns.pop()
    out.append(callee)
    return out
