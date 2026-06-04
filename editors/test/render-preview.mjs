// Renders a sample .fj program with the grammar + fj-dark colours to an SVG
// (and a PNG via the WASM @resvg/resvg-js) so the highlighting can be eyeballed
// without launching an editor. The colours are exactly those the VS Code
// extension applies and the JetBrains .tmTheme defines.
import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { BACKGROUND, styleForScopes } from "../colors.mjs";
import { loadFlipJumpGrammar, tokenize } from "../grammar.mjs";

const here = dirname(fileURLToPath(import.meta.url));

const SAMPLE = `// FlipJump syntax highlighting — fj-dark
dw = 2 * w

ns stl {
    def startup @ code_start {
        stl.startup code_start
      code_start:
    }
}

stl.startup
stl.output "Hello, World!\\n"
hex.add 0x10, a, 0b1010
;loop

segment 0x100
  reserve 8 * dw
loop:
    ;loop
`;

const FONT_SIZE = 16;
const CHAR_W = FONT_SIZE * 0.6;
const LINE_H = FONT_SIZE * 1.5;
const PAD = 16;

function esc(s) {
  return s
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

const grammar = await loadFlipJumpGrammar();
const lines = SAMPLE.replace(/\n$/, "").split("\n");

let maxCols = 0;
const svgLines = [];
// Tokenize the whole sample once so the rule stack flows across lines.
const allTokens = tokenize(grammar, SAMPLE.replace(/\n$/, ""));
const byLine = new Map();
for (const t of allTokens) {
  if (!byLine.has(t.line)) byLine.set(t.line, []);
  byLine.get(t.line).push(t);
}

lines.forEach((lineText, i) => {
  maxCols = Math.max(maxCols, lineText.length);
  const y = PAD + (i + 1) * LINE_H - LINE_H * 0.3;
  const spans = (byLine.get(i) || []).map((t) => {
    const { foreground, fontStyle } = styleForScopes(t.scopes);
    const weight = fontStyle === "bold" ? ' font-weight="bold"' : "";
    const italic = fontStyle === "italic" ? ' font-style="italic"' : "";
    return `<tspan fill="${foreground}"${weight}${italic}>${esc(t.text)}</tspan>`;
  });
  svgLines.push(
    `<text xml:space="preserve" x="${PAD}" y="${y.toFixed(1)}">${spans.join("")}</text>`,
  );
});

const width = Math.ceil(PAD * 2 + maxCols * CHAR_W);
const height = Math.ceil(PAD * 2 + lines.length * LINE_H);

const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
<rect width="100%" height="100%" fill="${BACKGROUND}"/>
<style>text { font-family: 'DejaVu Sans Mono','Consolas','Menlo','Courier New',monospace; font-size: ${FONT_SIZE}px; }</style>
${svgLines.join("\n")}
</svg>
`;

const svgPath = join(here, "preview.svg");
writeFileSync(svgPath, svg);
console.log(`wrote ${svgPath}`);

try {
  const { Resvg } = await import("@resvg/resvg-js");
  const resvg = new Resvg(svg, {
    background: BACKGROUND,
    font: { loadSystemFonts: true },
  });
  const png = resvg.render().asPng();
  const pngPath = join(here, "preview.png");
  writeFileSync(pngPath, png);
  console.log(`wrote ${pngPath}`);
} catch (err) {
  console.warn(`PNG rasterization skipped: ${err.message}`);
}
