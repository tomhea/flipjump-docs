package app.tomhe.flipjump;

import com.intellij.extapi.psi.ASTWrapperPsiElement;
import com.intellij.lang.ASTNode;
import com.intellij.lang.ParserDefinition;
import com.intellij.lang.PsiParser;
import com.intellij.lexer.Lexer;
import com.intellij.openapi.project.Project;
import com.intellij.psi.FileViewProvider;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.TokenType;
import com.intellij.psi.tree.IFileElementType;
import com.intellij.psi.tree.TokenSet;
import org.jetbrains.annotations.NotNull;

/**
 * Minimal parser definition: reuses {@link FlipJumpLexer} and builds a flat PSI
 * tree. Registering it (plugin.xml: {@code lang.parserDefinition}) is what makes
 * {@code PsiManager.findFile} / {@code PsiFile.findElementAt} return navigable
 * leaves — the targets {@link FlipJumpGotoDeclarationHandler} jumps to.
 */
public final class FlipJumpParserDefinition implements ParserDefinition {
    public static final IFileElementType FILE = new IFileElementType(FlipJumpLanguage.INSTANCE);

    private static final TokenSet WHITESPACE = TokenSet.create(TokenType.WHITE_SPACE);
    private static final TokenSet COMMENTS   = TokenSet.create(FlipJumpTokens.COMMENT);
    private static final TokenSet STRINGS    = TokenSet.create(FlipJumpTokens.STRING);

    @Override
    public @NotNull Lexer createLexer(Project project) {
        return new FlipJumpLexer();
    }

    @Override
    public @NotNull PsiParser createParser(Project project) {
        return new FlipJumpParser();
    }

    @Override
    public @NotNull IFileElementType getFileNodeType() {
        return FILE;
    }

    @Override
    public @NotNull TokenSet getWhitespaceTokens() {
        return WHITESPACE;
    }

    @Override
    public @NotNull TokenSet getCommentTokens() {
        return COMMENTS;
    }

    @Override
    public @NotNull TokenSet getStringLiteralElements() {
        return STRINGS;
    }

    @Override
    public @NotNull PsiElement createElement(ASTNode node) {
        return new ASTWrapperPsiElement(node);
    }

    @Override
    public @NotNull PsiFile createFile(@NotNull FileViewProvider viewProvider) {
        return new FlipJumpFile(viewProvider);
    }
}
