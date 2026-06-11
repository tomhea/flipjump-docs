package app.tomhe.flipjump;

import com.intellij.codeInsight.navigation.actions.GotoDeclarationHandler;
import com.intellij.openapi.editor.Document;
import com.intellij.openapi.editor.Editor;
import com.intellij.openapi.fileEditor.FileDocumentManager;
import com.intellij.openapi.project.DumbService;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.vfs.VirtualFile;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.PsiManager;
import com.intellij.psi.search.FileTypeIndex;
import com.intellij.psi.search.GlobalSearchScope;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Go-to-definition for FlipJump macros. Ctrl/Cmd+click (or Go to Declaration) on
 * a macro name jumps to its {@code def} — exactly like a project-wide search for
 * {@code def NAME }: every {@code .fj} file is scanned for a matching
 * declaration. One hit jumps straight there; several show the usual popup.
 *
 * <p>The word is the single dotted segment under the cursor, so clicking
 * {@code xor} in {@code hex.xor a b c} looks for {@code def xor} — the {@code hex.}
 * namespace prefix is dropped, because a macro is declared {@code def xor} inside
 * {@code ns hex}, never {@code def hex.xor}.
 */
public final class FlipJumpGotoDeclarationHandler implements GotoDeclarationHandler {

    @Override
    public PsiElement @Nullable [] getGotoDeclarationTargets(@Nullable PsiElement sourceElement,
                                                             int offset, @Nullable Editor editor) {
        if (sourceElement == null || editor == null) return null;
        // This is a global extension point fired for every language, so only act
        // on clicks inside a FlipJump file — otherwise we'd hijack go-to-decl in
        // other languages whenever a word coincides with a FlipJump macro name.
        if (!(sourceElement.getContainingFile() instanceof FlipJumpFile)) return null;
        Project project = sourceElement.getProject();
        // FileTypeIndex below needs the indexes; bail out gracefully while they
        // are still building rather than throwing IndexNotReadyException.
        if (DumbService.isDumb(project)) return null;

        String name = segmentAt(editor.getDocument().getCharsSequence(), offset);
        if (name == null) return null;

        // Optional indent, `def`, whitespace, then NAME with nothing identifier-
        // like after it: `(?![\w.])` rejects a trailing word char or dot, so this
        // matches `def xor` / `def xor{` but never `def xor2`, `redef xor`, or
        // `def xor.foo`.
        Pattern decl = Pattern.compile("(?m)^[ \\t]*def[ \\t]+(" + Pattern.quote(name) + ")(?![\\w.])");

        List<PsiElement> targets = new ArrayList<>();
        PsiManager psiManager = PsiManager.getInstance(project);
        FileDocumentManager docs = FileDocumentManager.getInstance();
        for (VirtualFile vf : FileTypeIndex.getFiles(FlipJumpFileType.INSTANCE,
                                                     GlobalSearchScope.projectScope(project))) {
            Document doc = docs.getDocument(vf);
            if (doc == null) continue;
            Matcher m = decl.matcher(doc.getCharsSequence());
            if (!m.find()) continue;
            PsiFile psiFile = psiManager.findFile(vf); // build PSI only for files with a hit
            if (psiFile == null) continue;
            do {
                PsiElement el = psiFile.findElementAt(m.start(1));
                if (el != null) targets.add(el);
            } while (m.find());
        }
        return targets.isEmpty() ? null : targets.toArray(PsiElement.EMPTY_ARRAY);
    }

    /** The FlipJump identifier segment around {@code offset} — letters/underscore
     *  then word chars, stopping at dots — or null if there isn't one. */
    private static @Nullable String segmentAt(CharSequence text, int offset) {
        int len = text.length();
        if (offset > len) offset = len;
        if (offset < 0) offset = 0;
        int start = offset, end = offset;
        while (start > 0 && isWordChar(text.charAt(start - 1))) start--;
        while (end < len && isWordChar(text.charAt(end))) end++;
        if (start == end) return null;
        char first = text.charAt(start);
        if (!(first == '_' || Character.isLetter(first))) return null; // not a number
        return text.subSequence(start, end).toString();
    }

    private static boolean isWordChar(char c) {
        return c == '_' || Character.isLetterOrDigit(c);
    }
}
