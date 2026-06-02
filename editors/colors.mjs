// The fj-dark colour map, copied from docs/_ext/fj_stl_extract/pygments_style.py
// (which itself mirrors the FlipJump IDE's Monaco `fj-dark` theme). Single
// source of truth for both the preview renderer and the VS Code
// configurationDefaults rules emitted at build time.
export const BACKGROUND = "#1e1e1e";
export const FOREGROUND = "#d4d4d4";

// scope -> { foreground, fontStyle? }. Order matters: the renderer picks the
// FIRST entry whose scope is present on a token (most-specific listed first).
export const SCOPE_COLORS = [
  ["entity.name.function.call.flipjump", { foreground: "#e8c47a" }],
  ["entity.name.function.flipjump", { foreground: "#56c8c8" }],
  ["entity.name.namespace.flipjump", { foreground: "#56c8c8" }],
  ["entity.name.label.flipjump", { foreground: "#4ec9b0" }],
  ["support.type.flipjump", { foreground: "#4ec9b0" }],
  ["keyword.other.directive.flipjump", { foreground: "#e07b39" }],
  ["keyword.control.flipjump", { foreground: "#569cd6", fontStyle: "bold" }],
  ["variable.other.constant.flipjump", { foreground: "#c792ea" }],
  ["variable.other.member.flipjump", { foreground: "#9cdcfe" }],
  ["variable.other.flipjump", { foreground: "#9cdcfe" }],
  ["constant.numeric.hex.flipjump", { foreground: "#b5cea8" }],
  ["constant.numeric.binary.flipjump", { foreground: "#b5cea8" }],
  ["constant.numeric.integer.flipjump", { foreground: "#b5cea8" }],
  ["string.quoted.double.flipjump", { foreground: "#ce9178" }],
  ["string.quoted.single.flipjump", { foreground: "#ce9178" }],
  ["comment.line.double-slash.flipjump", { foreground: "#6a9955", fontStyle: "italic" }],
  ["keyword.operator.flipjump", { foreground: "#d4d4d4" }],
  ["punctuation.flipjump", { foreground: "#d4d4d4" }],
];

// Given the scope stack on a token (outermost first), return the style of the
// first matching SCOPE_COLORS entry, or the default foreground.
export function styleForScopes(scopes) {
  for (const [scope, style] of SCOPE_COLORS) {
    if (scopes.includes(scope)) return style;
  }
  return { foreground: FOREGROUND };
}
