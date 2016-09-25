from _weakref import ref

from cnorm.nodes import *
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

    callback_decl = [
        "@callback"
        '(' id:name ')'

        #add_asp(name)
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
            |
            callback_decl
        ]
    """


# noinspection PyProtectedMember
@meta.hook(AspectC)
def add_asp(self, *args):
    if len(args) == 1:
        name = self.value(args[0])
        for m in self.rule_nodes.maps:
            body = m.get('_', None)
            if body is not None and isinstance(body, RootBlockStmt):
                root = body
                body = body.body
                for bod in body:
                    if hasattr(bod, '_name') and bod._name == name and hasattr(bod, 'body'):
                        ctype = PrimaryType(bod.ctype._identifier)
                        ctype._storage = 2
                        ctype._decltype = PointerType()
                        ctype._decltype._decltype = ParenType(bod.ctype._params)
                        # for par in ctype._decltype._decltype:
                        decl = Decl("callback_" + name, ctype)
                        body.append(decl)
                        root.types[decl._name] = ref(decl)

    else:
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
        if isinstance(rec.body[i], Do) and isinstance(rec.body[i].body, BlockStmt):
            recur_body(rec.body[i].body, v)
        if isinstance(rec.body[i], Switch) and isinstance(rec.body[i].body, BlockStmt):
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
    res = aspectC.parse_file("test2.c")

for t in b:
    for r in res.body:
        # noinspection PyProtectedMember
        if hasattr(r, '_name') and r._name == t[1] and hasattr(r, 'body') and hasattr(r.body, 'body'):
            if t[0] == "@begin":
                r.body.body = [t[2]] + r.body.body
            elif t[0] == "@end":
                r = r.body
                if not recur_body(r, t[2]):
                    r.body = r.body + [t[2]]


print(res.to_c())
