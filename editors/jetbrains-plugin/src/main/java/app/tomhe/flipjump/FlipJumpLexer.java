package app.tomhe.flipjump;

import com.intellij.lexer.LexerBase;
import com.intellij.psi.tree.IElementType;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Hand-written lexer that reproduces the FlipJump token classification of the
 * docs-site Pygments lexer / IDE Monaco tokenizer — the same ordered, position-
 * based rules as the shared TextMate grammar, so highlighting matches VS Code
 * exactly (including macro-call vs macro-def, which JetBrains' TextMate engine
 * cannot distinguish).
 *
 * Classification is stateless: each identifier is classified from its own text
 * plus local look-behind (preceding `def`/`ns`, line-start) and look-ahead
 * (trailing `=`/`:`, macro-call context), so incremental re-lexing is safe.
 */
public final class FlipJumpLexer extends LexerBase {
    private static final Set<String> KEYWORDS   = Set.of("def", "ns", "rep");
    private static final Set<String> DIRECTIVES = Set.of("pad", "reserve", "segment", "wflip");
    private static final Set<String> TYPES      = Set.of("dbit", "dw", "w");

    private static final Pattern STRING_DQ = Pattern.compile("\"([^\"\\\\]|\\\\.)*\"");
    private static final Pattern STRING_SQ = Pattern.compile("'([^'\\\\]|\\\\.)*'");
    private static final Pattern KEYWORD   = Pattern.compile("(?:def|ns|rep)\\b");
    private static final Pattern LEADING_DOT = Pattern.compile("\\.+[A-Za-z_][\\w.]*");
    private static final Pattern IDENT     = Pattern.compile("[A-Za-z_][\\w.]*");
    private static final Pattern HEX       = Pattern.compile("0[xX][0-9a-fA-F]+");
    private static final Pattern BIN       = Pattern.compile("0[bB][01]+");
    private static final Pattern INT       = Pattern.compile("\\d+");
    // Char-for-char port of the macro-call rule (negative-keyword lookahead +
    // name + trailing arg/comment/EOL lookahead). The name may carry leading
    // dots (`.zero`, `..foo`) and single dots between segments (`.a.b`), but
    // not consecutive dots after the first segment, and a lone `.` is not a
    // call. MULTILINE so `$` is EOL.
    private static final Pattern MACRO_CALL = Pattern.compile(
        "(?!(?:def|ns|rep|pad|reserve|segment|wflip|dbit|dw|w)\\b)\\.*[A-Za-z_]\\w*(?:\\.[A-Za-z_]\\w*)*"
            + "(?=[ \\t]+[^;\\s/]|[ \\t]*(?://|$))",
        Pattern.MULTILINE);

    private static final String PUNCTUATION_CHARS = ";,{}()[]";
    private static final String OPERATOR_CHARS = "!=<>?@^|%&*+-/:#$";

    private CharSequence buffer = "";
    private int bufferEnd;
    private int tokenStart;
    private int tokenEnd;
    private @Nullable IElementType tokenType;
    private final Matcher matcher = IDENT.matcher("");

    @Override
    public void start(@NotNull CharSequence buffer, int startOffset, int endOffset, int initialState) {
        this.buffer = buffer;
        this.bufferEnd = endOffset;
        this.tokenStart = startOffset;
        this.matcher.reset(buffer);
        locateToken();
    }

    @Override public int getState() { return 0; }
    @Override public @Nullable IElementType getTokenType() { return tokenType; }
    @Override public int getTokenStart() { return tokenStart; }
    @Override public int getTokenEnd() { return tokenEnd; }
    @Override public @NotNull CharSequence getBufferSequence() { return buffer; }
    @Override public int getBufferEnd() { return bufferEnd; }

    @Override
    public void advance() {
        this.tokenStart = this.tokenEnd;
        locateToken();
    }

    private char ch(int i) { return buffer.charAt(i); }

    /** Anchored match at pos; returns end offset or -1. */
    private int match(Pattern p, int pos) {
        matcher.usePattern(p);
        matcher.region(pos, bufferEnd);
        return matcher.lookingAt() ? matcher.end() : -1;
    }

    private boolean lookingAt(Pattern p, int pos) {
        matcher.usePattern(p);
        matcher.region(pos, bufferEnd);
        return matcher.lookingAt();
    }

    private void locateToken() {
        int pos = tokenStart;
        if (pos >= bufferEnd) { tokenType = null; tokenEnd = pos; return; }
        char c = ch(pos);

        // Line continuation: trailing backslash + newline -> whitespace.
        if (c == '\\' && pos + 1 < bufferEnd && ch(pos + 1) == '\n') {
            emit(FlipJumpTokens.WHITE_SPACE, pos + 2); return;
        }
        if (c == ' ' || c == '\t') {
            int e = pos + 1; while (e < bufferEnd && (ch(e) == ' ' || ch(e) == '\t')) e++;
            emit(FlipJumpTokens.WHITE_SPACE, e); return;
        }
        if (c == '\n' || c == '\r') {
            int e = pos + 1; while (e < bufferEnd && (ch(e) == '\n' || ch(e) == '\r')) e++;
            emit(FlipJumpTokens.WHITE_SPACE, e); return;
        }

        // Strings first, so quoted code (e.g. "def") is never re-interpreted.
        if (c == '"') { int m = match(STRING_DQ, pos); if (m > pos) { emit(FlipJumpTokens.STRING, m); return; } }
        if (c == '\'') { int m = match(STRING_SQ, pos); if (m > pos) { emit(FlipJumpTokens.STRING, m); return; } }

        // Line comment.
        if (c == '/' && pos + 1 < bufferEnd && ch(pos + 1) == '/') {
            int e = pos + 2; while (e < bufferEnd && ch(e) != '\n') e++;
            emit(FlipJumpTokens.COMMENT, e); return;
        }

        // Letter / underscore: keyword or identifier-family classification.
        if (isLetterOrUnderscore(c)) {
            int kw = match(KEYWORD, pos);
            if (kw > pos && KEYWORDS.contains(text(pos, kw))) { emit(FlipJumpTokens.KEYWORD, kw); return; }
            int end = match(IDENT, pos);
            emit(classifyIdent(pos, end, text(pos, end)), end);
            return;
        }

        // Leading-dot name (namespace navigation): .foo / ..bar / .a.b. At line
        // start with macro-call context it's a macro call (e.g. `.zero a b`);
        // otherwise a plain member reference.
        if (c == '.') {
            int m = match(LEADING_DOT, pos);
            if (m > pos) {
                if (isInMacroCallPosition(pos) && lookingAt(MACRO_CALL, pos)) {
                    emit(FlipJumpTokens.MACRO_CALL, m); return;
                }
                emit(FlipJumpTokens.IDENTIFIER, m); return;
            }
        }

        // Numbers.
        if (c >= '0' && c <= '9') {
            int m = match(HEX, pos); if (m > pos) { emit(FlipJumpTokens.NUMBER, m); return; }
            m = match(BIN, pos);     if (m > pos) { emit(FlipJumpTokens.NUMBER, m); return; }
            m = match(INT, pos);     if (m > pos) { emit(FlipJumpTokens.NUMBER, m); return; }
        }

        if (PUNCTUATION_CHARS.indexOf(c) >= 0) { emit(FlipJumpTokens.PUNCTUATION, pos + 1); return; }
        if (OPERATOR_CHARS.indexOf(c) >= 0)    { emit(FlipJumpTokens.OPERATOR, pos + 1); return; }

        emit(FlipJumpTokens.BAD_CHARACTER, pos + 1);
    }

    private IElementType classifyIdent(int pos, int end, String w) {
        if (isPrecededByWord(pos, "def")) return FlipJumpTokens.MACRO_DEF;
        if (isPrecededByWord(pos, "ns"))  return FlipJumpTokens.NAMESPACE;
        if (isInMacroCallPosition(pos) && lookingAt(MACRO_CALL, pos)) return FlipJumpTokens.MACRO_CALL;
        boolean bare = w.indexOf('.') < 0;          // constant/label LHS is dot-free
        if (bare && followedBy(end, '=')) return FlipJumpTokens.CONSTANT;
        if (bare && followedBy(end, ':')) return FlipJumpTokens.LABEL;
        if (DIRECTIVES.contains(w)) return FlipJumpTokens.DIRECTIVE;
        if (TYPES.contains(w))      return FlipJumpTokens.TYPE;
        return FlipJumpTokens.IDENTIFIER;
    }

    private void emit(IElementType type, int end) { tokenType = type; tokenEnd = end; }

    private String text(int start, int end) { return buffer.subSequence(start, end).toString(); }

    private static boolean isLetterOrUnderscore(char c) {
        return c == '_' || (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z');
    }

    private static boolean isWordChar(char c) {
        return c == '_' || Character.isLetterOrDigit(c);
    }

    /** True when only spaces/tabs (or nothing) precede {@code pos} on its line. */
    private boolean isAtLineStart(int pos) {
        int i = pos;
        while (i > 0 && (ch(i - 1) == ' ' || ch(i - 1) == '\t')) i--;
        return i == 0 || ch(i - 1) == '\n';
    }

    /** A statement-leading position where a macro call may appear: the line
     *  start, or just after a {@code )} — the close of a {@code rep(...)} clause,
     *  so {@code rep(n, i) bit.exact_xor ...} colours the call. (In valid
     *  FlipJump a {@code ) NAME args} sequence only arises after rep.) */
    private boolean isInMacroCallPosition(int pos) {
        if (isAtLineStart(pos)) return true;
        int i = pos;
        while (i > 0 && (ch(i - 1) == ' ' || ch(i - 1) == '\t')) i--;
        return i > 0 && ch(i - 1) == ')';
    }

    /** True when {@code word} immediately precedes {@code pos} (whitespace-separated). */
    private boolean isPrecededByWord(int pos, String word) {
        int i = pos, spaces = 0;
        while (i > 0 && (ch(i - 1) == ' ' || ch(i - 1) == '\t')) { i--; spaces++; }
        if (spaces == 0) return false;
        int wlen = word.length();
        if (i - wlen < 0) return false;
        for (int k = 0; k < wlen; k++) if (ch(i - wlen + k) != word.charAt(k)) return false;
        int before = i - wlen;
        return before == 0 || !isWordChar(ch(before - 1));
    }

    /** True when the next non-space char from {@code p} is {@code op}, not doubled. */
    private boolean followedBy(int p, char op) {
        int q = p; while (q < bufferEnd && (ch(q) == ' ' || ch(q) == '\t')) q++;
        return q < bufferEnd && ch(q) == op && (q + 1 >= bufferEnd || ch(q + 1) != op);
    }
}
