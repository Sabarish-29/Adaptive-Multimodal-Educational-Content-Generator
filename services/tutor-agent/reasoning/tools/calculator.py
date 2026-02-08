"""Calculator tool for the ReAct agent."""

import ast
import operator
from typing import Union

SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def safe_eval(expr: str) -> Union[float, int]:
    """Safely evaluate a math expression string."""
    tree = ast.parse(expr, mode="eval")
    return _eval_node(tree.body)


def _eval_node(node):
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return SAFE_OPS[type(node.op)](left, right)
    elif isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand)
        return SAFE_OPS[type(node.op)](operand)
    raise ValueError(f"Unsupported expression: {ast.dump(node)}")
