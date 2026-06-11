// Golden classification cases, ported one-for-one from the Pygments lexer
// contract at tests/test_extractor/test_pygments_lexer.py. The TextMate
// grammar must reproduce the same token classification so .fj files colour
// identically in VS Code / JetBrains and on the docs site / IDE.
//
// Each case has a `src` plus either:
//   find + expect      : the first token whose text === find must carry `expect`
//   find + expectNot    : that token must NOT carry `expectNot`
//   check(tokens)       : a custom predicate returning { ok, msg }

export const fixtures = [
  // ---- def / ns ----
  { name: "def NAME -> keyword + function", src: "def startup", find: "def", expect: "keyword.control.flipjump" },
  { name: "def NAME names the macro", src: "def startup", find: "startup", expect: "entity.name.function.flipjump" },
  { name: "ns NAME -> keyword + namespace", src: "ns stl", find: "ns", expect: "keyword.control.flipjump" },
  { name: "ns NAME names the namespace", src: "ns stl", find: "stl", expect: "entity.name.namespace.flipjump" },

  // ---- directives ----
  { name: "pad is a directive", src: "pad", find: "pad", expect: "keyword.other.directive.flipjump" },
  { name: "reserve is a directive", src: "reserve", find: "reserve", expect: "keyword.other.directive.flipjump" },
  { name: "segment is a directive", src: "segment", find: "segment", expect: "keyword.other.directive.flipjump" },
  { name: "wflip is a directive", src: "wflip", find: "wflip", expect: "keyword.other.directive.flipjump" },

  // ---- types ----
  { name: "dbit is a type", src: "dbit", find: "dbit", expect: "support.type.flipjump" },
  { name: "dw is a type", src: "dw", find: "dw", expect: "support.type.flipjump" },
  { name: "w is a type", src: "w", find: "w", expect: "support.type.flipjump" },
  { name: "bit is NOT a type (ns bit)", src: "ns bit", find: "bit", expectNot: "support.type.flipjump" },
  { name: "bit after ns is a namespace name", src: "ns bit", find: "bit", expect: "entity.name.namespace.flipjump" },

  // ---- labels / constants ----
  { name: "label classification", src: "code_start:", find: "code_start", expect: "entity.name.label.flipjump" },
  { name: "constant classification", src: "dw = 2 * w", find: "dw", expect: "variable.other.constant.flipjump" },
  {
    name: "equality op does not trigger constant rule",
    src: "; a == b",
    check: (toks) => {
      const hasConst = toks.some((t) => t.scopes.includes("variable.other.constant.flipjump"));
      const aPlain = toks.some((t) => t.text === "a" && t.scopes.includes("variable.other.flipjump"));
      const bPlain = toks.some((t) => t.text === "b" && t.scopes.includes("variable.other.flipjump"));
      return { ok: !hasConst && aPlain && bPlain, msg: `hasConst=${hasConst} aPlain=${aPlain} bPlain=${bPlain}` };
    },
  },

  // ---- strings (matched first) ----
  {
    name: "def inside a string is not a keyword",
    src: '"def foo"',
    check: (toks) => {
      const noKw = !toks.some((t) => t.scopes.includes("keyword.control.flipjump"));
      const isStr = toks.some((t) => t.text === '"def foo"' && t.scopes.includes("string.quoted.double.flipjump"));
      return { ok: noKw && isStr, msg: `noKeyword=${noKw} wholeString=${isStr}` };
    },
  },
  { name: "double-quoted string", src: '"hello"', find: '"hello"', expect: "string.quoted.double.flipjump" },
  { name: "single-quoted string", src: "'H'", find: "'H'", expect: "string.quoted.single.flipjump" },

  // ---- macro calls at line start ----
  { name: "macro call at line start", src: "stl.output_char 'H'", find: "stl.output_char", expect: "entity.name.function.call.flipjump" },
  { name: "dotted macro call with args", src: "stl.startup arg1, arg2", find: "stl.startup", expect: "entity.name.function.call.flipjump" },
  { name: "dotted ident mid-line is plain", src: "; stl.startup", find: "stl.startup", expect: "variable.other.flipjump" },
  { name: "leading-dot ident mid-line", src: "; .tables.x", find: ".tables.x", expect: "variable.other.member.flipjump" },

  // ---- leading-dot macro calls (line start) ----
  { name: "leading-dot macro call", src: ".zero a b", find: ".zero", expect: "entity.name.function.call.flipjump" },
  { name: "dotted leading-dot macro call", src: ".a.b arg", find: ".a.b", expect: "entity.name.function.call.flipjump" },
  { name: "multi-leading-dot macro call", src: "..foo x", find: "..foo", expect: "entity.name.function.call.flipjump" },
  {
    name: "a lone dot is never a macro call",
    src: ". arg",
    check: (toks) => {
      const anyCall = toks.some((t) => t.scopes.includes("entity.name.function.call.flipjump"));
      return { ok: !anyCall, msg: `anyCall=${anyCall} toks=${JSON.stringify(toks.map((t) => t.text))}` };
    },
  },
  {
    name: "consecutive dots after a name are not a macro call",
    src: ".a..b x",
    check: (toks) => {
      const call = toks.find((t) => t.scopes.includes("entity.name.function.call.flipjump"));
      const member = toks.find((t) => t.text === ".a..b" && t.scopes.includes("variable.other.member.flipjump"));
      return { ok: !call && !!member, msg: `call=${call ? JSON.stringify(call.text) : "none"} member=${!!member}` };
    },
  },

  // ---- macro calls inside a rep(...) clause ----
  { name: "macro call after rep clause", src: "rep(n, i) bit.exact_xor a, b", find: "bit.exact_xor", expect: "entity.name.function.call.flipjump" },
  { name: "leading-dot macro call after rep clause", src: "rep(n, i) .zero a", find: ".zero", expect: "entity.name.function.call.flipjump" },
  { name: "nested-paren rep count still finds the call", src: "rep((1<<n), i) foo a", find: "foo", expect: "entity.name.function.call.flipjump" },
  {
    name: "a close paren not followed by a name is not a macro call",
    src: "wflip (a), b",
    check: (toks) => {
      const anyCall = toks.some((t) => t.scopes.includes("entity.name.function.call.flipjump"));
      return { ok: !anyCall, msg: `anyCall=${anyCall}` };
    },
  },

  // ---- numbers ----
  { name: "hex number", src: "0xCAFE", find: "0xCAFE", expect: "constant.numeric.hex.flipjump" },
  { name: "binary number", src: "0b1010", find: "0b1010", expect: "constant.numeric.binary.flipjump" },
  { name: "decimal number", src: "12345", find: "12345", expect: "constant.numeric.integer.flipjump" },

  // ---- comment / punctuation / operators ----
  { name: "line comment", src: "// this is a comment", find: "// this is a comment", expect: "comment.line.double-slash.flipjump" },
  { name: "semicolon is punctuation", src: "f;j", find: ";", expect: "punctuation.flipjump" },
  { name: "plus is an operator", src: "a + b", find: "+", expect: "keyword.operator.flipjump" },

  // ---- real-world def line ----
  { name: "full def line: def keyword", src: "def startup code_start > IO {", find: "def", expect: "keyword.control.flipjump" },
  { name: "full def line: function name", src: "def startup code_start > IO {", find: "startup", expect: "entity.name.function.flipjump" },
  { name: "full def line: > is an operator", src: "def startup code_start > IO {", find: ">", expect: "keyword.operator.flipjump" },

  // ---- line continuation ----
  {
    name: "line continuation: backslash is not an operator, a/b present",
    src: "def foo a, \\\nb",
    check: (toks) => {
      const backslashAsOp = toks.some((t) => t.text === "\\" && t.scopes.includes("keyword.operator.flipjump"));
      const texts = toks.map((t) => t.text);
      return { ok: !backslashAsOp && texts.includes("a") && texts.includes("b"), msg: `backslashAsOp=${backslashAsOp} texts=${JSON.stringify(texts)}` };
    },
  },
];
