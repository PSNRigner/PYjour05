from cnorm.nodes import BlockStmt, If, While, For, Return
from pyrser import meta
from pyrser.grammar import Grammar
from cnorm.parsing.declaration import Declaration
# noinspection PyUnresolvedReferences
from cnorm.passes import to_c
import sys

b = []


class AspectC(Grammar, Declaration):
    entry = 'translation_unit'
    grammar = """
    asp_decl = [
        [ "@begin" | "@end" ]:tag
        '(' id:name ')'
        Statement.compound_statement:statement

        #add_asp(tag, name, statement)
    ]

    declaration = [
            ';' // garbage single comma
            |
            c_decl
            |
            preproc_decl
            |
            asm_decl
            |
            asp_decl
        ]
    """


@meta.hook(AspectC)
def add_asp(self, *args):
    b.append((self.value(args[0]), self.value(args[1]), args[2]))
    return True


def recur_body(rec, v):
    ok = False
    i = 0
    while i < len(rec.body):
        if isinstance(rec.body[i], If) and isinstance(rec.body[i].thencond, BlockStmt):
            recur_body(rec.body[i].thencond, v)
        if isinstance(rec.body[i], If) and isinstance(rec.body[i].elsecond, BlockStmt):
            recur_body(rec.body[i].elsecond, v)
        if isinstance(rec.body[i], While) and isinstance(rec.body[i].body, BlockStmt):
            recur_body(rec.body[i].body, v)
        if isinstance(rec.body[i], For) and isinstance(rec.body[i].body, BlockStmt):
            recur_body(rec.body[i].body, v)
        if isinstance(rec.body[i], Return):
            if i == 0:
                rec.body = [v] + rec.body
            else:
                rec.body = rec.body[:len(rec) - 1] + [v] + rec.body[i:]
            i += 1
            ok = True
        i += 1
    return ok


aspectC = AspectC()
if len(sys.argv) > 1:
    res = aspectC.parse_file(sys.argv[1])
else:
    res = aspectC.parse_file("test.c")

for t in b:
    # print(t[0], t[1], t[2].body)
    for r in res.body:
        # noinspection PyProtectedMember
        if hasattr(r, '_name') and r._name == t[1]:
            if t[0] == "@begin":
                r.body.body = [t[2]] + r.body.body
            elif t[0] == "@end":
                r = r.body
                if not recur_body(r, t[2]):
                    r.body = r.body + [t[2]]


print(res.to_c())
