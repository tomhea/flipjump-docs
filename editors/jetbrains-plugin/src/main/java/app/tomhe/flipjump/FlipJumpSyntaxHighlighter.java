package app.tomhe.flipjump;

import com.intellij.lexer.Lexer;
import com.intellij.openapi.editor.colors.TextAttributesKey;
import com.intellij.openapi.editor.markup.TextAttributes;
import com.intellij.openapi.fileTypes.SyntaxHighlighterBase;
import com.intellij.psi.tree.IElementType;
import org.jetbrains.annotations.NotNull;

import java.awt.Color;
import java.awt.Font;

import static com.intellij.openapi.editor.colors.TextAttributesKey.createTextAttributesKey;

/**
 * Maps each lexer token to its exact fj-dark colour (copied from the docs-site
 * Pygments style). The colours are embedded as the keys' default attributes, so
 * they apply out of the box in any colour scheme, scoped to FlipJump only.
 */
public final class FlipJumpSyntaxHighlighter extends SyntaxHighlighterBase {

    private static TextAttributesKey key(String name, String hex, int fontType) {
        TextAttributes attrs = new TextAttributes(Color.decode(hex), null, null, null, fontType);
        return createTextAttributesKey("FLIPJUMP_" + name, attrs);
    }

    public static final TextAttributesKey KEYWORD    = key("KEYWORD",    "#569cd6", Font.BOLD);
    public static final TextAttributesKey MACRO_DEF  = key("MACRO_DEF",  "#56c8c8", Font.PLAIN);
    public static final TextAttributesKey NAMESPACE  = key("NAMESPACE",  "#56c8c8", Font.PLAIN);
    public static final TextAttributesKey MACRO_CALL = key("MACRO_CALL", "#e8c47a", Font.PLAIN);
    public static final TextAttributesKey DIRECTIVE  = key("DIRECTIVE",  "#e07b39", Font.PLAIN);
    public static final TextAttributesKey TYPE       = key("TYPE",       "#4ec9b0", Font.PLAIN);
    public static final TextAttributesKey LABEL      = key("LABEL",      "#4ec9b0", Font.PLAIN);
    public static final TextAttributesKey CONSTANT   = key("CONSTANT",   "#c792ea", Font.PLAIN);
    public static final TextAttributesKey IDENTIFIER = key("IDENTIFIER", "#9cdcfe", Font.PLAIN);
    public static final TextAttributesKey NUMBER     = key("NUMBER",     "#b5cea8", Font.PLAIN);
    public static final TextAttributesKey STRING     = key("STRING",     "#ce9178", Font.PLAIN);
    public static final TextAttributesKey COMMENT    = key("COMMENT",    "#6a9955", Font.ITALIC);
    public static final TextAttributesKey OPERATOR   = key("OPERATOR",   "#d4d4d4", Font.PLAIN);

    private static final TextAttributesKey[] EMPTY = new TextAttributesKey[0];

    @Override
    public @NotNull Lexer getHighlightingLexer() {
        return new FlipJumpLexer();
    }

    @Override
    public TextAttributesKey @NotNull [] getTokenHighlights(IElementType t) {
        TextAttributesKey k = keyFor(t);
        return k == null ? EMPTY : new TextAttributesKey[]{k};
    }

    private static TextAttributesKey keyFor(IElementType t) {
        if (t == FlipJumpTokens.KEYWORD)     return KEYWORD;
        if (t == FlipJumpTokens.MACRO_DEF)   return MACRO_DEF;
        if (t == FlipJumpTokens.NAMESPACE)   return NAMESPACE;
        if (t == FlipJumpTokens.MACRO_CALL)  return MACRO_CALL;
        if (t == FlipJumpTokens.DIRECTIVE)   return DIRECTIVE;
        if (t == FlipJumpTokens.TYPE)        return TYPE;
        if (t == FlipJumpTokens.LABEL)       return LABEL;
        if (t == FlipJumpTokens.CONSTANT)    return CONSTANT;
        if (t == FlipJumpTokens.IDENTIFIER)  return IDENTIFIER;
        if (t == FlipJumpTokens.NUMBER)      return NUMBER;
        if (t == FlipJumpTokens.STRING)      return STRING;
        if (t == FlipJumpTokens.COMMENT)     return COMMENT;
        if (t == FlipJumpTokens.OPERATOR || t == FlipJumpTokens.PUNCTUATION) return OPERATOR;
        return null;
    }
}
