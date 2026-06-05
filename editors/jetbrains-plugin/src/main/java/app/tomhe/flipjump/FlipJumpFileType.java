package app.tomhe.flipjump;

import com.intellij.icons.AllIcons;
import com.intellij.openapi.fileTypes.LanguageFileType;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import javax.swing.Icon;

public final class FlipJumpFileType extends LanguageFileType {
    public static final FlipJumpFileType INSTANCE = new FlipJumpFileType();

    private FlipJumpFileType() {
        super(FlipJumpLanguage.INSTANCE);
    }

    @Override
    public @NotNull String getName() {
        return "FlipJump";
    }

    @Override
    public @NotNull String getDescription() {
        return "FlipJump assembly language";
    }

    @Override
    public @NotNull String getDefaultExtension() {
        return "fj";
    }

    @Override
    public @Nullable Icon getIcon() {
        return AllIcons.FileTypes.Text;
    }
}
