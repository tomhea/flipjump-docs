package app.tomhe.flipjump;

import com.intellij.psi.TokenType;
import com.intellij.psi.tree.IElementType;

/** Token kinds the lexer emits — one per fj-dark colour category. */
public interface FlipJumpTokens {
    IElementType KEYWORD     = new FlipJumpTokenType("KEYWORD");      // def / ns / rep
    IElementType MACRO_DEF   = new FlipJumpTokenType("MACRO_DEF");    // name after `def`
    IElementType NAMESPACE   = new FlipJumpTokenType("NAMESPACE");    // name after `ns`
    IElementType MACRO_CALL  = new FlipJumpTokenType("MACRO_CALL");   // line-start invocation
    IElementType DIRECTIVE   = new FlipJumpTokenType("DIRECTIVE");    // pad/reserve/segment/wflip
    IElementType TYPE        = new FlipJumpTokenType("TYPE");         // dbit/dw/w
    IElementType LABEL       = new FlipJumpTokenType("LABEL");        // foo:
    IElementType CONSTANT    = new FlipJumpTokenType("CONSTANT");     // foo =
    IElementType IDENTIFIER  = new FlipJumpTokenType("IDENTIFIER");
    IElementType NUMBER      = new FlipJumpTokenType("NUMBER");
    IElementType STRING      = new FlipJumpTokenType("STRING");
    IElementType COMMENT     = new FlipJumpTokenType("COMMENT");
    IElementType OPERATOR    = new FlipJumpTokenType("OPERATOR");
    IElementType PUNCTUATION = new FlipJumpTokenType("PUNCTUATION");

    IElementType BAD_CHARACTER = TokenType.BAD_CHARACTER;
    IElementType WHITE_SPACE   = TokenType.WHITE_SPACE;
}
