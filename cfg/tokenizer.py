"""
Tokenizer
"""
import re
from typing import List, Literal, Pattern
from .token import Token


class Tokenizer():
    """Tokenizer"""

    def __init__(self) -> None:
        self.token_infos: List[TokenInfo] = []
        self.tokens: List[Token] = []

    def add_regex(self, regex: str, token_type: Literal):
        """Add regular expression rule"""
        self.token_infos.append(TokenInfo(regex, token_type))

    def tokenize(self, string: str, line: int):
        """Strip the string into Tokens"""
        s = string.strip()
        self.tokens = []

        while s:
            match = None

            for token_info in self.token_infos:
                match = token_info.matcher.match(s)

                if match:
                    tok = match.group()
                    s = s.replace(tok, "", 1).strip()
                    self.tokens.append(Token(line, token_info.type, tok))
                    break

            if not match:
                raise TokenizerError("No match found for string: " + s)


class TokenInfo():
    """TokenInfo"""

    def __init__(self, regex: str, token_type: Literal) -> None:
        self.matcher: Pattern = re.compile(
            "^(" + regex + ")", flags=re.IGNORECASE)
        self.type = token_type


class TokenizerError(Exception):
    """Exception for Tokenizer"""
