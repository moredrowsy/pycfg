"""
Node
"""
from .token import Token


class Node:
    """Node"""

    def __init__(self, val: int, token: Token = None) -> None:
        self.val = val
        self.type = None
        self.tokens = [token] if token else []
        self.children = []
        self.parents = []

    def __repr__(self) -> str:
        return f"({self.val}) {self.type} {self.first_token()}"

    def __str__(self) -> str:
        s = f"({self.val})"

        if self.type:
            s += f"\n{self.type.name}"

        if self.tokens:
            s += "\n"

        for i in range(len(self.tokens)):
            if i > 0 and self.tokens[i-1].line == self.tokens[i].line:
                s += f" {self.tokens[i].sequence}"
            else:
                s += f"\n{self.tokens[i].sequence}"

        return s

    def __hash__(self) -> int:
        return self.val

    def __eq__(self, o: object) -> bool:
        if self is o:
            return True

        if self.__class__ is o.__class__:
            if self.val == o.val \
                    and self.type == o.type \
                    and len(self.tokens) == len(o.tokens):
                for i in range(len(self.tokens)):
                    if self.tokens[i] != o.tokens[i]:
                        return False
                return True

        return False

    def first_token(self):
        """Return first token in Node"""
        if self.tokens:
            return self.tokens[0]
        return "None"
