package app.tomhe.flipjump;

import com.intellij.psi.tree.IElementType;
import org.jetbrains.annotations.NotNull;

public final class FlipJumpTokenType extends IElementType {
    public FlipJumpTokenType(@NotNull String debugName) {
        super(debugName, FlipJumpLanguage.INSTANCE);
    }

    @Override
    public String toString() {
        return "FlipJump:" + super.toString();
    }
}
