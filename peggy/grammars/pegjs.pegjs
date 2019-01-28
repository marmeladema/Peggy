// The PEG.js grammar language.

Grammar     = Ws Code? Ws (Definition Ws)*


Code        = '{' (Code / !'}' .)* '}'


Definition  = Identifier Ws (CaseLiteral Ws)? '=' Ws Alternation Ws


Alternation = Sequence (Alt Sequence)*


Sequence    = Unit+


Unit        = ([a-zA-Z_] [a-zA-Z0-9_-]* ':')? Prefix*
               (  Identifier !(Ws '=') !(Ws CaseLiteral Ws '=')
               / Open Alternation Close
               / Literal
               / CaseLiteral
               / CharClass
               / WildCard ) Suffix? Ws Code? Ws


Prefix      = [$&!]


Suffix      = [?*+i]


Identifier  = [a-zA-Z_] [a-zA-Z0-9_-]*


Literal     = ['] (!['] (LChar / Hex / Unicode))+ ['] Ws


CaseLiteral = ["] (!["] (LChar / Hex / Unicode))+ ["] Ws


LChar       = '\\' [nrtvf'"\\] / !'\\' !EndOfLine .


CharClass   = '[' (!']' Range)* ']'


Range       = (Char / Hex / Unicode) ('-' (Char / Hex / Unicode))?


Char        = '\\' [nrtvf\-\]\\] / !'\\' !']' !EndOfLine .


Hex         = '\\<' [0-9A-Fa-f] [0-9A-Fa-f] '>'


Unicode     = '\\u' [0-9A-Fa-f] [0-9A-Fa-f] [0-9A-Fa-f] [0-9A-Fa-f]


WildCard    = '.' Ws


Alt         = '/' Ws


Open        = '(' Ws


Close       = ')' Ws


SComment    = '//' (!EndOfLine .)* (EndOfLine / !.)


MComment    = '/*' (MComment / !'*/' . )* '*/'


EndOfLine   = '\r\n' / '\n' / '\r'


Ws          = ([ \t] / EndOfLine / SComment / MComment)*
