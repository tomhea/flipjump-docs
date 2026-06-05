package app.tomhe.flipjump;

import com.intellij.icons.AllIcons;
import com.intellij.openapi.editor.colors.TextAttributesKey;
import com.intellij.openapi.fileTypes.SyntaxHighlighter;
import com.intellij.openapi.options.colors.AttributesDescriptor;
import com.intellij.openapi.options.colors.ColorDescriptor;
import com.intellij.openapi.options.colors.ColorSettingsPage;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import javax.swing.Icon;
import java.util.Map;

/** Settings → Editor → Color Scheme → FlipJump, so users can tweak the colours. */
public final class FlipJumpColorSettingsPage implements ColorSettingsPage {
    private static final AttributesDescriptor[] DESCRIPTORS = {
        new AttributesDescriptor("Keyword (def/ns/rep)", FlipJumpSyntaxHighlighter.KEYWORD),
        new AttributesDescriptor("Macro definition", FlipJumpSyntaxHighlighter.MACRO_DEF),
        new AttributesDescriptor("Namespace", FlipJumpSyntaxHighlighter.NAMESPACE),
        new AttributesDescriptor("Macro call", FlipJumpSyntaxHighlighter.MACRO_CALL),
        new AttributesDescriptor("Directive", FlipJumpSyntaxHighlighter.DIRECTIVE),
        new AttributesDescriptor("Type", FlipJumpSyntaxHighlighter.TYPE),
        new AttributesDescriptor("Label", FlipJumpSyntaxHighlighter.LABEL),
        new AttributesDescriptor("Constant", FlipJumpSyntaxHighlighter.CONSTANT),
        new AttributesDescriptor("Identifier", FlipJumpSyntaxHighlighter.IDENTIFIER),
        new AttributesDescriptor("Number", FlipJumpSyntaxHighlighter.NUMBER),
        new AttributesDescriptor("String", FlipJumpSyntaxHighlighter.STRING),
        new AttributesDescriptor("Comment", FlipJumpSyntaxHighlighter.COMMENT),
        new AttributesDescriptor("Operator / punctuation", FlipJumpSyntaxHighlighter.OPERATOR),
    };

    @Override public @Nullable Icon getIcon() { return AllIcons.FileTypes.Text; }

    @Override public @NotNull SyntaxHighlighter getHighlighter() { return new FlipJumpSyntaxHighlighter(); }

    @Override
    public @NotNull String getDemoText() {
        return "// FlipJump syntax highlighting\n" +
               "dw = 2 * w\n\n" +
               "ns stl {\n" +
               "    def startup @ code_start {\n" +
               "        stl.startup code_start\n" +
               "      code_start:\n" +
               "    }\n" +
               "}\n\n" +
               "stl.output \"Hello, World!\\n\"\n" +
               "hex.add 0x10, a, 0b1010\n" +
               "segment 0x100\n" +
               "  reserve 8 * dw\n";
    }

    @Override
    public @Nullable Map<String, TextAttributesKey> getAdditionalHighlightingTagToDescriptorMap() {
        return null;
    }

    @Override public AttributesDescriptor @NotNull [] getAttributeDescriptors() { return DESCRIPTORS; }

    @Override public ColorDescriptor @NotNull [] getColorDescriptors() { return ColorDescriptor.EMPTY_ARRAY; }

    @Override public @NotNull String getDisplayName() { return "FlipJump"; }
}
