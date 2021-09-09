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
