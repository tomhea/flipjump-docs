"""Recursive-descent parser for FlipJump source.

Produces a FLAT list of `MacroNode` / `ConstantNode` records — namespace
nesting is collapsed into a `namespace_path` tuple on each node. Macro
bodies are kept as opaque token lists; the dependency walker in
`dep_graph.py` reads them.

Grammar (informal):

    file        := stmt*
    stmt        := namespace | macro | constant | OTHER
    namespace   := 'ns' IDENT '{' stmt* '}'
    macro       := 'def' IDENT params? ('@' idents)? ('<' refs)? ('>' idents)? '{' body '}'
    constant    := IDENT '=' expr_until_newline
    body        := <opaque, brace-matched>
    OTHER       := anything else, consumed silently up to the next statement boundary
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .tokenizer import Token, TokenKind, tokenize

__all__ = [
    "FileNode",
    "MacroNode",
    "ConstantNode",
    "ParseError",
    "parse",
]


class ParseError(RuntimeError):
    def __init__(self, msg: str, token: Token):
        super().__init__(f"{msg} at line {token.line} col {token.col} (got {token.kind.name} {token.text!r})")
        self.token = token


@dataclass
class MacroNode:
    name: str
    namespace_path: tuple[str, ...]
    params: list[str]
    locals_: list[str]
    requires_labels: list[str]
    exports_labels: list[str]
    body_tokens: list[Token]
    start_line: int
    end_line: int

    @property
    def arity(self) -> int:
        return len(self.params)

    @property
    def fq_name(self) -> str:
        if self.namespace_path:
            return ".".join(self.namespace_path) + "." + self.name
        return self.name


@dataclass
class ConstantNode:
    name: str
    namespace_path: tuple[str, ...]
    expr_tokens: list[Token]
    start_line: int

    @property
    def fq_name(self) -> str:
        if self.namespace_path:
            return ".".join(self.namespace_path) + "." + self.name
        return self.name


@dataclass
class FileNode:
    macros: list[MacroNode] = field(default_factory=list)
    constants: list[ConstantNode] = field(default_factory=list)


def parse(source: str) -> FileNode:
    tokens = [t for t in tokenize(source)]
    return _Parser(tokens).parse_file()


class _Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0
        self.ns_stack: list[str] = []
        self.file = FileNode()

    # ---------- low-level cursor ----------

    def peek(self, offset: int = 0) -> Token:
        i = self.pos + offset
        if i >= len(self.tokens):
            return self.tokens[-1]  # EOF
        return self.tokens[i]

    def advance(self) -> Token:
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def skip_trivia(self) -> None:
        """Drop NEWLINE and COMMENT tokens (used at statement boundaries)."""
        while self.peek().kind in (TokenKind.NEWLINE, TokenKind.COMMENT):
            self.pos += 1

    # ---------- entry ----------

    def parse_file(self) -> FileNode:
        while self.peek().kind != TokenKind.EOF:
            self.skip_trivia()
            t = self.peek()
            if t.kind == TokenKind.EOF:
                break
            if t.kind == TokenKind.KEYWORD and t.text == "ns":
                self._parse_namespace()
            elif t.kind == TokenKind.KEYWORD and t.text == "def":
                self._parse_macro()
            elif t.kind == TokenKind.IDENT and self._is_constant_assignment():
                self._parse_constant()
            else:
                # Unknown top-level construct (label, expression, directive,
                # etc.). Skip until newline so we don't loop forever, but
                # do not raise — the STL has constructs we don't model.
                self._skip_to_statement_end()
        return self.file

    # ---------- ns ... { ... } ----------

    def _parse_namespace(self) -> None:
        self.advance()  # consume 'ns'
        name_tok = self.peek()
        if name_tok.kind != TokenKind.IDENT:
            raise ParseError("expected namespace name after 'ns'", name_tok)
        self.advance()
        self.skip_trivia()
        if self.peek().kind != TokenKind.LBRACE:
            raise ParseError("expected '{' after namespace name", self.peek())
        self.advance()  # consume '{'
        self.ns_stack.append(name_tok.text)
        try:
            while self.peek().kind != TokenKind.EOF:
                self.skip_trivia()
                t = self.peek()
                if t.kind == TokenKind.RBRACE:
                    self.advance()
                    return
                if t.kind == TokenKind.KEYWORD and t.text == "ns":
                    self._parse_namespace()
                elif t.kind == TokenKind.KEYWORD and t.text == "def":
                    self._parse_macro()
                elif t.kind == TokenKind.IDENT and self._is_constant_assignment():
                    self._parse_constant()
                else:
                    self._skip_to_statement_end()
            # EOF before matching '}' — accept silently rather than raise,
            # so malformed files don't break the whole extraction.
        finally:
            self.ns_stack.pop()

    # ---------- def NAME params @ locals < requires > exports { body } ----------

    def _parse_macro(self) -> None:
        start_line = self.peek().line
        self.advance()  # consume 'def'
        name_tok = self.peek()
        if name_tok.kind != TokenKind.IDENT:
            raise ParseError("expected macro name after 'def'", name_tok)
        self.advance()

        # Read params until @, <, >, or {.
        params = self._read_ident_list_until({TokenKind.AT, TokenKind.LT,
                                              TokenKind.GT, TokenKind.LBRACE})

        locals_: list[str] = []
        requires_labels: list[str] = []
        exports_labels: list[str] = []

        # The signature clauses can appear in any order in source,
        # though `@`/`<`/`>` is the typical sequence.
        while self.peek().kind in (TokenKind.AT, TokenKind.LT, TokenKind.GT):
            tok = self.advance()
            stop = {TokenKind.AT, TokenKind.LT, TokenKind.GT, TokenKind.LBRACE}
            stop.discard(tok.kind)
            items = self._read_ident_list_until(stop)
            if tok.kind == TokenKind.AT:
                locals_.extend(items)
            elif tok.kind == TokenKind.LT:
                requires_labels.extend(items)
            else:  # GT
                exports_labels.extend(items)

        if self.peek().kind != TokenKind.LBRACE:
            raise ParseError("expected '{' after macro signature", self.peek())
        body_tokens, end_line = self._capture_brace_balanced_body()

        self.file.macros.append(MacroNode(
            name=name_tok.text,
            namespace_path=tuple(self.ns_stack),
            params=params,
            locals_=locals_,
            requires_labels=requires_labels,
            exports_labels=exports_labels,
            body_tokens=body_tokens,
            start_line=start_line,
            end_line=end_line,
        ))

    def _read_ident_list_until(self, stop_kinds: set[TokenKind]) -> list[str]:
        items: list[str] = []
        # Drop leading commas/newlines between adjacent clauses.
        while True:
            self.skip_trivia()
            t = self.peek()
            if t.kind in stop_kinds or t.kind == TokenKind.EOF:
                return items
            if t.kind == TokenKind.COMMA:
                self.advance()
                continue
            if t.kind == TokenKind.IDENT:
                items.append(t.text)
                self.advance()
                continue
            # An unexpected token in the signature — stop reading items.
            return items

    def _capture_brace_balanced_body(self) -> tuple[list[Token], int]:
        """Consume `{` ... matching `}`. Returns (body tokens, end line).

        The braces themselves are NOT included in the returned tokens.
        Strings are token-level so their braces never affect the count.
        """
        assert self.peek().kind == TokenKind.LBRACE
        self.advance()  # consume `{`
        depth = 1
        body: list[Token] = []
        end_line = self.peek().line
        while self.peek().kind != TokenKind.EOF:
            t = self.peek()
            if t.kind == TokenKind.LBRACE:
                depth += 1
            elif t.kind == TokenKind.RBRACE:
                depth -= 1
                if depth == 0:
                    end_line = t.line
                    self.advance()
                    return body, end_line
            body.append(t)
            self.advance()
        # EOF without matching `}` — return what we have.
        return body, end_line

    # ---------- IDENT = expr (constant at namespace top level) ----------

    def _is_constant_assignment(self) -> bool:
        """Return True if `current_ident COMMENT? '='` matches on the
        same logical line.

        Constants only appear as `NAME = expr` at top level / namespace
        top level. We must not be loose enough to treat
        `IDENT \n stuff = ...` as a constant — only same-line `=` counts.
        Inline comments (`IDENT // comment =`) are tolerated since
        nothing in source legitimately uses that form.
        """
        if self.peek().kind != TokenKind.IDENT:
            return False
        i = self.pos + 1
        # Skip COMMENT tokens but NOT NEWLINE — the `=` must be on the
        # same logical line as the identifier.
        while i < len(self.tokens) and self.tokens[i].kind == TokenKind.COMMENT:
            i += 1
        return i < len(self.tokens) and self.tokens[i].kind == TokenKind.EQUALS

    def _parse_constant(self) -> None:
        name_tok = self.advance()
        self.skip_trivia()
        assert self.peek().kind == TokenKind.EQUALS
        self.advance()  # consume '='
        # Capture expression tokens until newline (with line continuations
        # already collapsed by the tokenizer) or EOF.
        expr_tokens: list[Token] = []
        while self.peek().kind not in (TokenKind.NEWLINE, TokenKind.EOF):
            t = self.peek()
            if t.kind == TokenKind.COMMENT:
                self.advance()
                continue
            expr_tokens.append(t)
            self.advance()
        self.file.constants.append(ConstantNode(
            name=name_tok.text,
            namespace_path=tuple(self.ns_stack),
            expr_tokens=expr_tokens,
            start_line=name_tok.line,
        ))

    # ---------- recovery ----------

    def _skip_to_statement_end(self) -> None:
        """Skip past one unknown statement.

        Statement end heuristic: the next NEWLINE at the current depth, or
        a brace-balanced expression if we hit a `{`. This is good enough
        for the constructs we don't model (labels, free directives).
        """
        depth = 0
        while self.peek().kind != TokenKind.EOF:
            t = self.peek()
            if t.kind == TokenKind.LBRACE:
                depth += 1
            elif t.kind == TokenKind.RBRACE:
                if depth == 0:
                    return  # let caller consume
                depth -= 1
            elif t.kind == TokenKind.NEWLINE and depth == 0:
                self.advance()
                return
            self.advance()
