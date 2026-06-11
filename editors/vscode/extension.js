"use strict";

// Go-to-definition for FlipJump macros.
//
// Ctrl+click (or F12 / "Go to Definition") on a macro name jumps to where it's
// declared. FlipJump has no symbol table we can rely on, so — exactly like a
// project-wide content search for `def NAME ` — we scan every `.fj` file in the
// workspace for a matching `def NAME` declaration and return those positions.
//
// The word under the cursor is the single dotted segment, so clicking `xor` in
// `hex.xor a b c` looks for `def xor` (the namespace prefix is intentionally
// dropped — a macro is declared `def xor` *inside* `ns hex`, never
// `def hex.xor`). One match jumps straight there; several show a peek list.

const vscode = require("vscode");

// A FlipJump identifier segment: letters/underscore then word chars, no dots.
// Passing this to getWordRangeAtPosition overrides the language's dotted
// wordPattern, so `hex.xor` yields just the clicked segment.
const SEGMENT = /[A-Za-z_]\w*/;

/** A `def NAME` declaration: optional indent, `def`, whitespace, then the exact
 *  name with nothing identifier-like after it — `(?![\w.])` rejects both a
 *  trailing word char and a trailing dot, so `def xor` matches `def xor` /
 *  `def xor{` but never `def xor2`, `redef xor`, or `def xor.foo`. */
function declarationRegex(name) {
  return new RegExp("^[ \\t]*def[ \\t]+" + escapeRegExp(name) + "(?![\\w.])");
}

function escapeRegExp(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * @param {vscode.TextDocument} document
 * @param {vscode.Position} position
 * @param {vscode.CancellationToken} token
 */
async function provideDefinition(document, position, token) {
  const range = document.getWordRangeAtPosition(position, SEGMENT);
  if (!range) return undefined;
  const name = document.getText(range);
  const re = declarationRegex(name);

  // Scan every .fj file in the workspace, plus the current document (covers the
  // single-file / no-folder case, where findFiles returns nothing). The explicit
  // exclude skips node_modules but, by being explicit, also overrides the user's
  // files.exclude/search.exclude — so a `def` in an otherwise-hidden folder is
  // still found.
  const uris = await vscode.workspace.findFiles("**/*.fj", "**/node_modules/**");
  if (!uris.some((u) => u.toString() === document.uri.toString())) {
    uris.push(document.uri);
  }

  const locations = [];
  for (const uri of uris) {
    if (token.isCancellationRequested) return undefined;
    let doc;
    try {
      doc = await vscode.workspace.openTextDocument(uri);
    } catch {
      continue; // unreadable / binary — skip
    }
    const lines = doc.getText().split(/\r\n|\r|\n/);
    for (let i = 0; i < lines.length; i++) {
      const m = re.exec(lines[i]);
      if (m) {
        // The match ends right after NAME, so NAME starts here.
        const col = m[0].length - name.length;
        locations.push(
          new vscode.Location(uri, new vscode.Position(i, col))
        );
      }
    }
  }
  return locations;
}

function activate(context) {
  context.subscriptions.push(
    vscode.languages.registerDefinitionProvider("flipjump", {
      provideDefinition,
    })
  );
}

function deactivate() {}

module.exports = { activate, deactivate };
