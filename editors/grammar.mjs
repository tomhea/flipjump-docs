// Loads the canonical FlipJump TextMate grammar into a vscode-textmate
// Registry backed by the WASM oniguruma engine — the same tokenizer stack
// VS Code and the JetBrains TextMate plugin use, so the scopes produced here
// are exactly what those editors produce.
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);

// vscode-oniguruma and vscode-textmate are CommonJS; require() exposes their
// named exports reliably under ESM (a plain `import *` lands them on .default).
const oniguruma = require("vscode-oniguruma");
const vsctm = require("vscode-textmate");

let registryPromise;

async function makeRegistry() {
  const wasmPath = require.resolve("vscode-oniguruma/release/onig.wasm");
  const wasmBin = readFileSync(wasmPath).buffer;
  await oniguruma.loadWASM(wasmBin);
  const onigLib = Promise.resolve({
    createOnigScanner: (patterns) => new oniguruma.OnigScanner(patterns),
    createOnigString: (s) => new oniguruma.OnigString(s),
  });
  return new vsctm.Registry({
    onigLib,
    loadGrammar: async (scopeName) => {
      if (scopeName !== "source.flipjump") return null;
      const text = readFileSync(
        join(here, "grammars", "flipjump.tmLanguage.json"),
        "utf8",
      );
      return vsctm.parseRawGrammar(text, "flipjump.tmLanguage.json");
    },
  });
}

export async function loadFlipJumpGrammar() {
  if (!registryPromise) registryPromise = makeRegistry();
  const registry = await registryPromise;
  return registry.loadGrammar("source.flipjump");
}

// Tokenize a (possibly multi-line) source string. Returns a flat list of
// { line, text, scopes } for every token, with the rule stack carried across
// lines exactly as an editor would.
export function tokenize(grammar, source) {
  const out = [];
  let ruleStack = vsctm.INITIAL;
  const lines = source.split("\n");
  lines.forEach((lineText, lineNo) => {
    const result = grammar.tokenizeLine(lineText, ruleStack);
    for (const t of result.tokens) {
      out.push({
        line: lineNo,
        text: lineText.substring(t.startIndex, t.endIndex),
        scopes: t.scopes,
      });
    }
    ruleStack = result.ruleStack;
  });
  return out;
}
