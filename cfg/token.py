"""
Token
"""
from enum import Enum


class Token():
    """Token"""

    def __init__(self, line: int, token_type: Enum, sequence: str) -> None:
        self.line = line
        self.type = token_type
        self.sequence = sequence

    def __repr__(self) -> str:
        return f"l: {self.line} t: {self.type} s: {self.sequence}"

    def __eq__(self, o: object) -> bool:
        if self is o:
            return True

        if self.__class__ is o.__class__ \
                and self.line == o.line \
                and self.type == o.type \
                and self.sequence == self.sequence:
            return True

        return False
