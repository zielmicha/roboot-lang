import roboot_parser as parser
import ast
from typing import Any, Tuple, Union, List

bin_ops = {
    '+': ast.Add,
    '-': ast.Add,
    '*': ast.Mult,
    '/': ast.Div,
    '//': ast.FloorDiv,
    '%': ast.Mod,
    '|': ast.BitOr,
    '&': ast.BitAnd,
}

def translate_expr(e):
    if isinstance(e, parser.Ident):
        return ast.Name(id=e.val, ctx=ast.Load())
    elif isinstance(e, parser.Const):
        if isinstance(e.val, str):
            return ast.Str(s=e.val)
        elif isinstance(e.val, bytes):
            return ast.Bytes(s=e.val)
        else:
            return ast.Num(n=e.val)
    elif isinstance(e, parser.Op):
        if e.op in bin_ops:
            return ast.BinOp(op=bin_ops[e.op](), left=translate_expr(e.left), right=translate_expr(e.right))
        else:
            assert 0, e
    else:
        assert 0, e
