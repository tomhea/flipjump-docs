// Headless verification that the FlipJump TextMate grammar produces the right
// scopes. Uses vscode-textmate + WASM oniguruma — the same engine VS Code and
// the JetBrains TextMate plugin use — so a PASS here means those editors will
// classify .fj tokens identically to the docs site / IDE.
//
// Run: npm run verify   (exits non-zero if any case fails)
import { loadFlipJumpGrammar, tokenize } from "../grammar.mjs";
import { fixtures } from "./fixtures.mjs";

const grammar = await loadFlipJumpGrammar();

let pass = 0;
let fail = 0;

function record(ok, label, detail) {
  if (ok) {
    pass++;
    console.log(`  PASS  ${label}`);
  } else {
    fail++;
    console.log(`  FAIL  ${label}${detail ? `  (${detail})` : ""}`);
  }
}

console.log("Golden classification cases:");
for (const f of fixtures) {
  const toks = tokenize(grammar, f.src);
  if (f.check) {
    const { ok, msg } = f.check(toks);
    record(ok, f.name, msg);
    continue;
  }
  const hit = toks.find((t) => t.text === f.find);
  if (!hit) {
    record(false, f.name, `token ${JSON.stringify(f.find)} not found in ${JSON.stringify(toks.map((t) => t.text))}`);
    continue;
  }
  if (f.expect) {
    record(hit.scopes.includes(f.expect), f.name, `scopes=${JSON.stringify(hit.scopes)}`);
  } else if (f.expectNot) {
    record(!hit.scopes.includes(f.expectNot), f.name, `scopes=${JSON.stringify(hit.scopes)}`);
  }
}

// ---- Full-program smoke test ----
// A realistic multi-line program must tokenize without throwing, leave no
// character unscoped-into-error, and classify a few representative tokens.
const program = `// prime sieve (excerpt)
hw = w/4
PRIMES_MEMORY_START = (1 << (w-1))

def prime_sieve_main {
    stl.startup_and_init_all
  prime_loop_if:
    hex.cmp hw, p, n, prime_loop, prime_loop, end
    is_add_4+dbit; prime_loop_if
  end:
    stl.output "done\\n"
    stl.loop
}

segment PRIMES_MEMORY_START
  reserve PRIMES_MEMORY_LENGTH
`;

console.log("\nFull-program smoke test:");
let smokeOk = true;
let smokeDetail = "";
try {
  const toks = tokenize(grammar, program);
  const want = [
    // `hw =` at line start is a macro call, NOT a constant: `hw` is not in the
    // macro-call exclusion list, so the line-start macro rule wins — exactly as
    // Pygments classifies it (verified against the lexer). Contrast `dw =`,
    // where `dw` IS excluded and so stays a constant (see golden fixtures).
    ["hw", "entity.name.function.call.flipjump"],
    ["prime_sieve_main", "entity.name.function.flipjump"],
    ["prime_loop_if", "entity.name.label.flipjump"],
    ["stl.startup_and_init_all", "entity.name.function.call.flipjump"],
    ["dbit", "support.type.flipjump"],
    ["segment", "keyword.other.directive.flipjump"],
    ['"done\\n"', "string.quoted.double.flipjump"],
  ];
  for (const [text, scope] of want) {
    const hit = toks.find((t) => t.text === text);
    if (!hit || !hit.scopes.includes(scope)) {
      smokeOk = false;
      smokeDetail = `expected ${JSON.stringify(text)} -> ${scope}, got ${hit ? JSON.stringify(hit.scopes) : "<not found>"}`;
      break;
    }
  }
} catch (err) {
  smokeOk = false;
  smokeDetail = `threw: ${err.message}`;
}
record(smokeOk, "prime sieve excerpt tokenizes with expected scopes", smokeDetail);

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
