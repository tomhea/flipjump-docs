// Copies the canonical grammar into the VS Code extension so that it never
// carries a hand-edited divergent copy. CI runs `npm run sync && git diff
// --exit-code` to enforce that the committed copy is byte-identical to the
// canonical source.
import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

const copies = [
  ["grammars/flipjump.tmLanguage.json", "vscode/syntaxes/flipjump.tmLanguage.json"],
];

for (const [from, to] of copies) {
  const dst = join(here, to);
  mkdirSync(dirname(dst), { recursive: true });
  copyFileSync(join(here, from), dst);
  console.log(`synced ${from} -> ${to}`);
}
