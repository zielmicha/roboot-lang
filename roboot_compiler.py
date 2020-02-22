from dataclasses import dataclass
from typing import NamedTuple, Any, Tuple, Union, List
import dlog
import roboot_parser as parser
import roboot_python_ast

@dataclass(frozen=True, eq=False)
class IrNode:
    pass

@dataclass(frozen=True, eq=False)
class IrRelation(IrNode):
    rel: Any
    axis_names: List[str]

@dataclass(frozen=True, eq=False)
class IrIntersect(IrNode):
    a: Any
    b: Any

    @staticmethod
    def make(lst): # O(n^2)!
        if len(lst) == 1: return lst
        return IrIntersect(lst[0], IrIntersect.make(lst[1:]))

@dataclass(frozen=True, eq=False)
class IrUnion(IrNode):
    a: Any
    b: Any

@dataclass(frozen=True, eq=False)
class IrIntroduce(IrNode):
    a: Any
    name: str

def ir_get_axis_names(ir_node, result):
    if isinstance(ir_node, IrIntersect):
        ir_get_axis_names(ir_node.a, result)
        ir_get_axis_names(ir_node.b, result)
        return (
            sorted(set(result[ir_node.a]) & set(result[ir_node.b])) +
            sorted(set(result[ir_node.a]) - set(result[ir_node.b])) +
            sorted(set(result[ir_node.b]) - set(result[ir_node.a])))
    elif isinstance(ir_node, IrRelation):
        result[ir_node] = ir_node.axis_names
    else:
        assert False

def compile_ir(ir_node, axis_names):
    if isinstance(ir_node, IrIntersect):
        a_names = axis_names[ir_node.a]
        b_names = axis_names[ir_node.b]
        a_arity = len(a_names)
        b_arity = len(a_names)
        join_k = len(intersection_list)
        intersection_set = set(a_names) & set(b_names)
        intersection_list = a_names[:join_k]
        assert set(intersection_list) == intersection_set

        a_proj = dlog.Projection(ir_node.a, [ a_names.index(name) for name in intersection_list[:a_arity] ])
        b_proj = dlog.Projection(ir_node.b, [ b_names.index(name) for name in intersection_list[:join_k] + intersection_list[a_arity:] ])
        return dlog.Join(a_proj, b_proj, join_k)
    elif isinstance(ir_node, IrRelation):
        return ir_node.rel
    elif isinstance(ir_node, IrUnion):
        left = ir_node.left
        right = ir_node.right
        if set(axis_names[left]) != set(axis_names[right]): # ???
            raise Exception('inconsistent variables %r != %r' % (set(axis_names[left]), set(axis_names[right])))

        return dlog.Union(
            left,
            Projection(right, [ axis_names[right].index(name) for name in axis_names[left] ]))
    else:
        assert False

class GenSym: pass

def get_relation_for_bool_func(func, arity):
    if isinstance(func, dlog.Relation):
        assert func.arity == arity
        return func
    else:
        assert 0, func

def get_relation_for_func(func, arity):
    assert 0

def relation_for_op(op):
    assert 0, op

class Compiler:
    def __init__(self, module):
        self.module = module
        self.top_arg_names = None

    def compile_relation_expr_aux(self, node, arg_names, additional_relations):
        if isinstance(node, parser.Ident):
            if node.str in arg_names:
                return node.str
            else:
                # TODO: how to handle const?
                result = GenSym()
                value = getattr(self.module, node.str)
                additional_relations.append(IrRelation(rel=dlog.ConstRelation(value), axis_names=[result]))
                return result
        elif isinstance(node, parse.FuncCall):
            func_obj = self.expr_eval(node.func)
            args_values = [
                self.compile_relation_expr_aux(arg, arg_names, additional_relations)
                for arg in func_obj.args
            ]
            relation = get_relation_for_func(func_obj, len(func_obj.args))
            result = GenSym()
            additional_relations.append(IrRelation(relation, [
                *arg_values,
                result
            ]))
            return result
        elif isinstance(node, parse.Op):
            result = GenSym()
            additional_relations.append(IrRelation(relation_for_op(node.op), [
                *arg_values,
                result
            ]))
        else:
            assert False

    def compile_relation_expr(self, node):
        additional_relations = []
        return self.compile_relation_expr_aux(node, self.top_arg_names, additional_relations), additional_relations

    def expr_eval(self, e):
        ast = roboot_python_ast.translate_expr(e)
        return ast

    def compile_relation(self, node):
        if isinstance(node, parser.FuncCall):
            func = self.expr_eval(node.func)
            rel = get_relation_for_bool_func(func, len(node.args))

            additional_relations = []
            transformed_args = []
            for arg in node.args:
                transformed_arg_name, rels = compile_relation_expr(arg)
                additional_relations += rels
                transformed_args.append(transformed_arg_name)

            return IrJoin.make([IrRelation(rel, transformed_args)] + additional_relations)
        elif isinstance(node, parser.Op):
            if node.op == 'and':
                return IrIntersect(self.compile_relation(node.left), self.compile_relation(node.right))
            elif node.op == 'or':
                return IrUnion(self.compile_relation(node.left), self.compile_relation(node.right))
            elif node.op == '==':
                left_var, additional_1 = self.compile_relation_expr(node.left)
                right_var, additional_2 = self.compile_relation_expr(node.left)

                return IrJoin.make([
                    *additional_1,
                    IrRelation(dlog.Eq(), [left_var, right_var]),
                    *additional_2,
                ])
            else:
                raise Exception('%r is not supported as a relation (boolean) operator' % node.op)
        else:
            assert 0, node

    def compile_stmt(self, stmt):
        if isinstance(stmt, ERelation):
            expected_args = stmt.head.args
            ir_relation = self.compile_relation(stmt.body)

            arg_names = {}
            ir_get_axis_names(ir_relation, arg_names)


            for arg in expected_args:
                if relation.
        else:
            assert 0, stmt

def compile_module(code):
    stmts = parser.parse(parser.ESuite, code)
    module = {}

    for stmt in stmts:
        Compiler(module).compile_stmt(stmt)
