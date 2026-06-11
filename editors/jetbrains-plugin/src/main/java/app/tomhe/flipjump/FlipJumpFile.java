package app.tomhe.flipjump;

import com.intellij.extapi.psi.PsiFileBase;
import com.intellij.openapi.fileTypes.FileType;
import com.intellij.psi.FileViewProvider;
import org.jetbrains.annotations.NotNull;

/** PSI root for a .fj file. Lets the platform build a navigable tree over the
 *  lexer's tokens (see {@link FlipJumpParserDefinition}). */
public final class FlipJumpFile extends PsiFileBase {
    public FlipJumpFile(@NotNull FileViewProvider viewProvider) {
        super(viewProvider, FlipJumpLanguage.INSTANCE);
    }

    @Override
    public @NotNull FileType getFileType() {
        return FlipJumpFileType.INSTANCE;
    }

    @Override
    public String toString() {
        return "FlipJump File";
    }
}
