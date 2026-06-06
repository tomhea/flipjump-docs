package app.tomhe.flipjump;

import com.intellij.lexer.Lexer;
import com.intellij.openapi.editor.colors.TextAttributesKey;
import com.intellij.openapi.fileTypes.SyntaxHighlighterBase;
import com.intellij.psi.tree.IElementType;
import org.jetbrains.annotations.NotNull;

import static com.intellij.openapi.editor.colors.TextAttributesKey.createTextAttributesKey;

/**
 * Maps each lexer token to its exact fj-dark colour. The default colours live in
 * the bundled colour schemes (resources/colorSchemes/FlipJump*.xml, registered
 * via {@code additionalTextAttributes} in plugin.xml), so the keys are created
 * by external name only — no deprecated hard-coded {@code TextAttributes}.
 */
public final class FlipJumpSyntaxHighlighter extends SyntaxHighlighterBase {

    private static TextAttributesKey key(String name) {
        return createTextAttributesKey("FLIPJUMP_" + name);
    }

    public static final TextAttributesKey KEYWORD    = key("KEYWORD");
    public static final TextAttributesKey MACRO_DEF  = key("MACRO_DEF");
    public static final TextAttributesKey NAMESPACE  = key("NAMESPACE");
    public static final TextAttributesKey MACRO_CALL = key("MACRO_CALL");
    public static final TextAttributesKey DIRECTIVE  = key("DIRECTIVE");
    public static final TextAttributesKey TYPE       = key("TYPE");
    public static final TextAttributesKey LABEL      = key("LABEL");
    public static final TextAttributesKey CONSTANT   = key("CONSTANT");
    public static final TextAttributesKey IDENTIFIER = key("IDENTIFIER");
    public static final TextAttributesKey NUMBER     = key("NUMBER");
    public static final TextAttributesKey STRING     = key("STRING");
    public static final TextAttributesKey COMMENT    = key("COMMENT");
    public static final TextAttributesKey OPERATOR   = key("OPERATOR");

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
