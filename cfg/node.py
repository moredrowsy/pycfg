"""
Node
"""
from .token import Token


class Node:
    """Node"""

    def __init__(self, val, token: Token = None) -> None:
        self.val = val
        self.type = None
        self.tokens = [token] if token else []
        self.children = []
        self.parents = []

    def __repr__(self) -> str:
        return f"({self.val}) {self.type} {self.first_token()}"

    def first_token(self):
        """Return first token in Node"""
        if self.tokens:
            return self.tokens[0]
        return "None"
