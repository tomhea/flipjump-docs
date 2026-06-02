// Copies the canonical grammar + theme into the per-editor packages so that
// editors/vscode and editors/jetbrains never carry a hand-edited divergent
// copy. CI runs `npm run sync && git diff --exit-code` to enforce that the
// committed copies are byte-identical to the canonical sources.
import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

const copies = [
  ["grammars/flipjump.tmLanguage.json", "vscode/syntaxes/flipjump.tmLanguage.json"],
  ["grammars/flipjump.tmLanguage.json", "jetbrains/flipjump.tmLanguage.json"],
  ["flipjump-dark.tmTheme", "jetbrains/flipjump-dark.tmTheme"],
];

for (const [from, to] of copies) {
  const dst = join(here, to);
  mkdirSync(dirname(dst), { recursive: true });
  copyFileSync(join(here, from), dst);
  console.log(`synced ${from} -> ${to}`);
}
