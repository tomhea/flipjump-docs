package app.tomhe.flipjump;

import com.intellij.lang.ASTNode;
import com.intellij.lang.PsiBuilder;
import com.intellij.lang.PsiParser;
import com.intellij.psi.tree.IElementType;
import org.jetbrains.annotations.NotNull;

/**
 * Trivial parser. The plugin has a lexer but no grammar, so we just wrap the
 * whole token stream under the file root. That gives every .fj file a real PSI
 * tree (one leaf per token) — enough for {@code findElementAt} and go-to-
 * definition. Highlighting stays lexer-based and independent of this.
 */
public final class FlipJumpParser implements PsiParser {
    @Override
    public @NotNull ASTNode parse(@NotNull IElementType root, @NotNull PsiBuilder builder) {
        PsiBuilder.Marker rootMarker = builder.mark();
        while (!builder.eof()) {
            builder.advanceLexer();
        }
        rootMarker.done(root);
        return builder.getTreeBuilt();
    }
}
