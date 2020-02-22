import tokenize, io, ast
from parsercombinators import combinator, ForwardDecl, joined_with, optional, many
import parsercombinators
from dataclasses import dataclass
from typing import Any, List, Tuple, Dict, Optional

def token(t):
    def f(text):
        if text and text[0].type == t: return (), text[1:]
    return combinator(f)

def token_s(t):
    def f(text):
        if text and text[0].type == t: return (text[0].string,), text[1:]
    return combinator(f)

def op(s):
    def f(text):
        if text and text[0].type == tokenize.OP and text[0].string == s: return (), text[1:]
    return combinator(f)

def op_s(s):
    def f(text):
        if text and text[0].type == tokenize.OP and text[0].string in s: return (text[0].string, ), text[1:]
    return combinator(f)

def keyword_s(s):
    def f(text):
        if text and text[0].type == tokenize.NAME and text[0].string in s: return (text[0].string, ), text[1:]
    return combinator(f)

def keyword(s):
    def f(text):
        if text and text[0].type == tokenize.NAME and text[0].string == s: return (), text[1:]
    return combinator(f)

def name():
    def f(text):
        if text and text[0].type == tokenize.NAME: return (text[0].string,), text[1:]
    return combinator(f)

ERelationArg = (
    name()
)

@dataclass
class AstNode:
    pass

@dataclass
class RelationHead(AstNode):
    name: str
    args: List[Any]

@dataclass
class RelationDef(AstNode):
    head: RelationHead
    body: Any

ERelationHead = (
    keyword('relation') + name() + op('(') + optional(joined_with(op(','), ERelationArg)).wrap() + op(')')
).map(lambda x: (RelationHead(name=x[0], args=x[1]),))

@dataclass
class Op(AstNode):
    op: str
    left: Any
    right: Any

@dataclass
class Const(AstNode):
    val: str

@dataclass
class Ident(AstNode):
    val: str

@dataclass
class Call(AstNode):
    ident: Any
    args: Any

def make_op(o):
    v = o[0]
    for i in range(1, len(o), 2):
        v = Op(op=o[i], left=v, right=o[i+1])
    return v

def by_priority(inner, ops):
    for op in reversed(ops):
        inner = joined_with(op, inner).map(lambda a: (make_op(a),), )

    return inner

@dataclass
class FuncArg(AstNode):
    value: Any
    keyword_arg_name: Optional[str]

@dataclass
class FuncCall(AstNode):
    func: Any
    args: List[FuncArg]

@dataclass
class IfStmt(AstNode):
    branches: List[Tuple[Any, Any]]
    else_branch: Optional[Any]

@dataclass
class StmtList(AstNode):
    stmts: List[Any]

EExpr = ForwardDecl()

EFuncArg = (
    EExpr.map(lambda v: (FuncArg(value=v[0], keyword_arg_name=None),)) |
    (name() + op('=') + EExpr).map(lambda v: (FuncArg(value=v[0], keyword_arg_name=v[1]),))
)

EFuncArgs = joined_with(op(','), EFuncArg)

EIdent = token_s(tokenize.NAME)

EExprAtom = (
    (op('(') + EExpr + op(')')) |
    token_s(tokenize.NUMBER).map(lambda a: (Const(val=ast.literal_eval(a[0])), )) |
    EIdent.map(lambda a: (Ident(a[0]), ))
)

EExprCall = ForwardDecl()

def make_expr_call(args):
    val = args[0]
    for x in args[1:]: val = FuncCall(func=val, args=x)
    return (val, )

EExprCall.value = (
    EExprAtom + many(op('(') + EFuncArgs + op(')'))
).map(make_expr_call)

EExprOp = by_priority(EExprCall, [
    keyword_s(['or', 'and', 'in', 'is']),
    op_s(['<','>','==','>=','<=','<>','!=']),
    op_s(['+', '-']),
    op_s(['*', '/', '//']),
    op_s(['**']),
])

EExpr.value = (
    EExprOp
)

ERelation = (
    ERelationHead +
    op('=') +
    EExpr
)

ESimpleStmt = ForwardDecl()

EStmt = ForwardDecl()

ESuite = (
    ESimpleStmt |
    (token(tokenize.NEWLINE) + token(tokenize.INDENT) + many(EStmt, 1).wrap() + token(tokenize.DEDENT)).map(lambda x: (StmtList(x), ))
)

def make_if(e):
    branches = []
    for i in range(0, len(e), 2):
        branches.append(e[i : i + 2])

    else_branch = None
    if len(e) % 2 == 1:
        else_branch = e[-1]

    return (IfStmt(branches=branches, else_branch=else_branch), )

EIfStmt = (
    keyword('if') + EExpr + op(':') + ESuite +
    many(keyword('elif') + EExpr + op(':') + ESuite) +
    optional(keyword('else') + op(':') + ESuite)).map(make_if)

EWhileStmt = keyword('while') + EExpr + op(':') + ESuite + optional(keyword('else') + op(':') + ESuite)

ESmallStmt = (
    EExpr |
    (EExpr + op_s(['+=', '-=', '*=', '@=', '/=', '%=', '&=', '^=',
                   '<<=', '>>=', '**=', '//=']) + EExpr) |
    ERelation
)

ESimpleStmt.value = joined_with(op(';'), ESmallStmt) + token(tokenize.NEWLINE)

EStmt.value = (
    ESimpleStmt |
    EWhileStmt |
    EIfStmt)

def parse(cat, text):
    tokens = list(tokenize.tokenize(io.BytesIO(text.encode()).readline))
    #print(tokens)
    cat = cat + optional(token(tokenize.NEWLINE)) + token(tokenize.ENDMARKER)
    return parsercombinators.run(cat, [ t for t in tokens if t.type not in (tokenize.ENCODING, ) ])

if __name__ == '__main__':
    print(parse(ERelationHead, 'relation foo()'))
    print(parse(ERelationHead, 'relation foo(xoxo, zoo)'))
    print(parse(EExpr, '1 + 2 * 3'))
    print(parse(EExpr, '(1 + 2) is 3'))
    print(parse(EStmt, '1 + 2 * 3'))
    print(parse(EStmt, 'print(5); print(10)'))
    print(parse(EStmt, 'if 0: 5'))
    print(parse(EStmt, 'if 0:\n  5\n  6'))
    print(parse(ERelation, 'relation foo() = xoo'))
    #print(parse(EStmt, 'if 0:' + '\n  5'*500))
