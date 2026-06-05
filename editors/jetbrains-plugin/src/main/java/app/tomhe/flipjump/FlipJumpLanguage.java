package app.tomhe.flipjump;

import com.intellij.lang.Language;

public final class FlipJumpLanguage extends Language {
    public static final FlipJumpLanguage INSTANCE = new FlipJumpLanguage();

    private FlipJumpLanguage() {
        super("FlipJump");
    }
}
