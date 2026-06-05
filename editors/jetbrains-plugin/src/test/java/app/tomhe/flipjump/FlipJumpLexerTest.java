package app.tomhe.flipjump;

import com.intellij.psi.tree.IElementType;
import org.junit.Test;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertSame;

/**
 * Parity with the docs-site Pygments lexer contract
 * (tests/test_extractor/test_pygments_lexer.py) — the same golden cases the
 * shared TextMate grammar is verified against, so the native plugin classifies
 * tokens identically to VS Code and the docs.
 */
public class FlipJumpLexerTest {

    /** Type of the first token whose exact text equals {@code needle}. */
    private static @org.jetbrains.annotations.Nullable IElementType typeOf(String src, String needle) {
        FlipJumpLexer lx = new FlipJumpLexer();
        lx.start(src, 0, src.length(), 0);
        while (lx.getTokenType() != null) {
            if (src.substring(lx.getTokenStart(), lx.getTokenEnd()).equals(needle)) {
                return lx.getTokenType();
            }
            lx.advance();
        }
        return null;
    }

    private static boolean anyTokenHasType(String src, IElementType type) {
        FlipJumpLexer lx = new FlipJumpLexer();
        lx.start(src, 0, src.length(), 0);
        while (lx.getTokenType() != null) {
            if (lx.getTokenType() == type) return true;
            lx.advance();
        }
        return false;
    }

    @Test public void defName() {
        assertSame(FlipJumpTokens.KEYWORD, typeOf("def startup", "def"));
        assertSame(FlipJumpTokens.MACRO_DEF, typeOf("def startup", "startup"));
    }

    @Test public void nsName() {
        assertSame(FlipJumpTokens.KEYWORD, typeOf("ns stl", "ns"));
        assertSame(FlipJumpTokens.NAMESPACE, typeOf("ns stl", "stl"));
    }

    @Test public void directives() {
        for (String d : new String[]{"pad", "reserve", "segment", "wflip"}) {
            assertSame(d, FlipJumpTokens.DIRECTIVE, typeOf(d, d));
        }
    }

    @Test public void types() {
        for (String t : new String[]{"dbit", "dw", "w"}) {
            assertSame(t, FlipJumpTokens.TYPE, typeOf(t, t));
        }
    }

    @Test public void bitIsNotAType() {
        assertSame(FlipJumpTokens.NAMESPACE, typeOf("ns bit", "bit"));
    }

    @Test public void label() {
        assertSame(FlipJumpTokens.LABEL, typeOf("code_start:", "code_start"));
    }

    @Test public void constant() {
        assertSame(FlipJumpTokens.CONSTANT, typeOf("dw = 2 * w", "dw"));
    }

    @Test public void equalityIsNotAConstant() {
        assertFalse(anyTokenHasType("; a == b", FlipJumpTokens.CONSTANT));
        assertSame(FlipJumpTokens.IDENTIFIER, typeOf("; a == b", "a"));
    }

    @Test public void defInsideStringIsNotKeyword() {
        assertSame(FlipJumpTokens.STRING, typeOf("\"def foo\"", "\"def foo\""));
        assertFalse(anyTokenHasType("\"def foo\"", FlipJumpTokens.KEYWORD));
    }

    @Test public void macroCallAtLineStart() {
        assertSame(FlipJumpTokens.MACRO_CALL, typeOf("stl.output_char 'H'", "stl.output_char"));
        assertSame(FlipJumpTokens.MACRO_CALL, typeOf("stl.startup arg1, arg2", "stl.startup"));
    }

    @Test public void dottedIdentMidLineIsPlain() {
        assertSame(FlipJumpTokens.IDENTIFIER, typeOf("; stl.startup", "stl.startup"));
    }

    @Test public void leadingDotIdentMidLine() {
        assertSame(FlipJumpTokens.IDENTIFIER, typeOf("; .tables.x", ".tables.x"));
    }

    @Test public void numbers() {
        assertSame(FlipJumpTokens.NUMBER, typeOf("0xCAFE", "0xCAFE"));
        assertSame(FlipJumpTokens.NUMBER, typeOf("0b1010", "0b1010"));
        assertSame(FlipJumpTokens.NUMBER, typeOf("12345", "12345"));
    }

    @Test public void strings() {
        assertSame(FlipJumpTokens.STRING, typeOf("\"hello\"", "\"hello\""));
        assertSame(FlipJumpTokens.STRING, typeOf("'H'", "'H'"));
    }

    @Test public void comment() {
        assertSame(FlipJumpTokens.COMMENT, typeOf("// this is a comment", "// this is a comment"));
    }

    @Test public void semicolonIsPunctuation() {
        assertSame(FlipJumpTokens.PUNCTUATION, typeOf("f;j", ";"));
    }

    @Test public void plusIsOperator() {
        assertSame(FlipJumpTokens.OPERATOR, typeOf("a + b", "+"));
    }

    /** The documented line-start quirk: `hw =` is a macro call (hw not excluded),
     *  while `dw =` stays a constant (dw is excluded) — exact lexer parity. */
    @Test public void lineStartAssignIsMacroCallUnlessExcluded() {
        assertSame(FlipJumpTokens.MACRO_CALL, typeOf("hw = w/4", "hw"));
        assertSame(FlipJumpTokens.CONSTANT, typeOf("dw = 2 * w", "dw"));
    }
}
