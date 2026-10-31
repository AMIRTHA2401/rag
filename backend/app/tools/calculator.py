import ast
import operator

from langchain_core.tools import tool

_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod, ast.USub: operator.neg}


def _evaluate(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_evaluate(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_evaluate(node.left), _evaluate(node.right))
    raise ValueError("Only numeric arithmetic expressions are allowed")


@tool
def calculator_tool(expression: str) -> str:
    """Safely calculate a numeric arithmetic expression."""
    if len(expression) > 200:
        raise ValueError("Expression is too long")
    return str(_evaluate(ast.parse(expression, mode="eval").body))

