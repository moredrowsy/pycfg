# pylint: disable=too-many-lines
"""
Parser
"""
from collections import deque
from enum import auto
from typing import Deque, List
from .enum import OrderedEnum
from .node import Node
from .token import Token
from .tokenizer import Tokenizer, TokenizerError


class TokenState(OrderedEnum):
    """TokenState"""
    ERROR = 0
    INIT_START = auto()
    FUNCTION = auto()
    STATEMENT = auto()
    SEMICOLON = auto()
    WHILE = auto()
    DO = auto()
    FOR = auto()
    IF = auto()
    ELSE = auto()
    PAREN_OPEN = auto()
    PAREN_CLOSE = auto()
    BRACE_OPEN = auto()
    BRACE_CLOSE = auto()
    LAMBDA = auto()


class FSMState(OrderedEnum):
    """FSMState"""
    ERROR = 0

    INIT_START = auto()

    # STATEMENT STATES
    STATEMENT_START = auto()
    STATEMENT_MID = auto()
    STATEMENT_END = auto()

    # IF-THEN-ELSE
    IF_START = auto()
    IF_PAREN_OPEN = auto()
    IF_PAREN_STATEMENT = auto()
    IF_PAREN_CLOSE = auto()
    IF_THEN_BRACE_OPEN = auto()
    IF_THEN_STATEMENT = auto()
    IF_THEN_SINGLE_STATEMENT = auto()
    IF_THEN_END = auto()

    ELSE_IF_STATEMENT = auto()
    ELSE_IF_END = auto()

    IF_ELSE = auto()
    IF_ELSE_BRACE_OPEN = auto()
    IF_ELSE_STATEMENT = auto()
    IF_ELSE_SINGLE_STATEMENT = auto()
    IF_ELSE_END = auto()

    # WHILE STATES
    WHILE_START = auto()
    WHILE_PAREN_OPEN = auto()
    WHILE_PAREN_STATEMENT = auto()
    WHILE_PAREN_CLOSE = auto()
    WHILE_BRACE_OPEN = auto()
    WHILE_STATEMENT = auto()
    WHILE_SINGLE_STATEMENT = auto()
    WHILE_END = auto()

    # DO_WHILE STATES
    DO_WHILE_START = auto()
    DO_WHILE_BRACE_OPEN = auto()
    DO_WHILE_STATEMENT = auto()
    DO_WHILE_BRACE_CLOSE = auto()
    DO_WHILE_KEYWORD = auto()
    DO_WHILE_PAREN_OPEN = auto()
    DO_WHILE_PAREN_STATEMENT = auto()
    DO_WHILE_PAREN_CLOSE = auto()
    DO_WHILE_END = auto()

    # FOR LOOPS
    FOR_START = auto()
    FOR_PAREN_OPEN = auto()
    FOR_INIT = auto()
    FOR_INIT_END = auto()
    FOR_COND = auto()
    FOR_COND_END = auto()
    FOR_MODIFY = auto()
    FOR_PAREN_CLOSE = auto()
    FOR_BRACE_OPEN = auto()
    FOR_STATEMENT = auto()
    FOR_SINGLE_STATEMENT = auto()
    FOR_END = auto()

    # FUNCTION STATES
    FUNC_START = auto()
    FUNC_BRACE_OPEN = auto()
    FUNC_STATEMENT = auto()
    FUNC_END = auto()


class DecompStates(OrderedEnum):
    """DecompStates"""
    # CASE
    C1 = 0
    C1_END = auto()

    # IF-THEN
    D0 = auto()
    D0_END = auto()

    # IF-THEN-ELSE
    D1 = auto()
    D1_END = auto()

    # WHILE-DO
    D2 = auto()
    D2_END = auto()

    # DO-WHILE
    D3 = auto()
    D3_END = auto()

    # FUNCTION
    F1 = auto()
    F1_END = auto()

    # STATEMENT
    P1 = auto()


class Parser():
    """Parser"""

    def __init__(self) -> None:
        self.tokenizer = Tokenizer()
        self.tokens = deque([])
        self.strings: List[str] = []
        self.nodes: List[Node] = []
        self.states = None
        self._init_tokenizer()
        self._init_states()

    def _init_tokenizer(self) -> None:
        self.tokenizer.add_regex(r";", TokenState.SEMICOLON)
        self.tokenizer.add_regex(r"if", TokenState.IF)
        self.tokenizer.add_regex(r"else", TokenState.ELSE)
        self.tokenizer.add_regex(r"while", TokenState.WHILE)
        self.tokenizer.add_regex(r"do", TokenState.DO)
        self.tokenizer.add_regex(r"for", TokenState.FOR)
        self.tokenizer.add_regex(r"[^\(\)\;\{\}]*[\s]*[^\(\)\;\{\}]+\([^\(\)\;\{\}]*\)",
                                 TokenState.FUNCTION)
        self.tokenizer.add_regex(r"\(", TokenState.PAREN_OPEN)
        self.tokenizer.add_regex(r"\)", TokenState.PAREN_CLOSE)
        self.tokenizer.add_regex(r"\{", TokenState.BRACE_OPEN)
        self.tokenizer.add_regex(r"\}", TokenState.BRACE_CLOSE)
        self.tokenizer.add_regex(r"[^\(\)\{\}\;]+", TokenState.STATEMENT)

    def _init_states(self) -> None:
        # Initialize 2D finite state machine
        self.states = [[FSMState.ERROR] *
                       len(TokenState) for _ in range(len(FSMState))]

        # Mark initial states
        self._add_state_rule(FSMState.INIT_START, TokenState.ERROR,
                             FSMState.ERROR)
        self._add_state_rule(FSMState.INIT_START, TokenState.STATEMENT,
                             FSMState.STATEMENT_START)
        self._add_state_rule(FSMState.INIT_START, TokenState.SEMICOLON,
                             FSMState.STATEMENT_START)
        self._add_state_rule(FSMState.INIT_START, TokenState.IF,
                             FSMState.IF_START)
        self._add_state_rule(FSMState.INIT_START, TokenState.WHILE,
                             FSMState.WHILE_START)
        self._add_state_rule(FSMState.INIT_START, TokenState.DO,
                             FSMState.DO_WHILE_START)
        self._add_state_rule(FSMState.INIT_START, TokenState.FOR,
                             FSMState.FOR_START)
        self._add_state_rule(FSMState.INIT_START, TokenState.FUNCTION,
                             FSMState.FUNC_START)

        # Mark FSM table
        self.init_statement_states()
        self.init_while_states()
        self.init_do_while_states()
        self.init_if_states()
        self.init_for_states()
        self.init_function_states()

    def init_statement_states(self) -> None:
        """Init FSM states"""
        # STATEMENT_START -> STATEMENT -> STATEMENT_MID
        self._add_state_rule(FSMState.STATEMENT_START, TokenState.STATEMENT,
                             FSMState.STATEMENT_MID)
        # STATEMENT_MID -> STATEMENT -> STATEMENT_MID
        self._add_state_rule(FSMState.STATEMENT_MID, TokenState.STATEMENT,
                             FSMState.STATEMENT_MID)
        # STATEMENT_MID -> SEMICOLON -> STATEMENT_END
        self._add_state_rule(FSMState.STATEMENT_MID, TokenState.SEMICOLON,
                             FSMState.STATEMENT_END)
        # STATEMENT_START -> SEMICOLON -> STATEMENT_END
        self._add_state_rule(FSMState.STATEMENT_START, TokenState.SEMICOLON,
                             FSMState.STATEMENT_END)
        # STATEMENT_END -> STATEMENT -> STATEMENT_MID
        self._add_state_rule(FSMState.STATEMENT_END, TokenState.STATEMENT,
                             FSMState.STATEMENT_MID)
        # STATEMENT_END -> SEMICOLON -> STATEMENT_MID
        self._add_state_rule(FSMState.STATEMENT_END, TokenState.SEMICOLON,
                             FSMState.STATEMENT_END)

    def init_while_states(self) -> None:
        """Init FSM states"""
        # WHILE_START -> PAREN_OPEN -> WHILE_PAREN_OPEN
        self._add_state_rule(FSMState.WHILE_START, TokenState.PAREN_OPEN,
                             FSMState.WHILE_PAREN_OPEN)
        # WHILE_PAREN_OPEN -> STATEMENT -> WHILE_PAREN_STATEMENT
        self._add_state_rule(FSMState.WHILE_PAREN_OPEN, TokenState.STATEMENT,
                             FSMState.WHILE_PAREN_STATEMENT)
        # WHILE_PAREN_STATEMENT -> STATEMENT -> WHILE_PAREN_STATEMENT
        self._add_state_rule(FSMState.WHILE_PAREN_STATEMENT, TokenState.STATEMENT,
                             FSMState.WHILE_PAREN_STATEMENT)
        # WHILE_PAREN_STATEMENT -> STATEMENT -> WHILE_PAREN_CLOSE
        self._add_state_rule(FSMState.WHILE_PAREN_STATEMENT, TokenState.PAREN_CLOSE,
                             FSMState.WHILE_PAREN_CLOSE)
        # WHILE_PAREN_STATEMENT -> DO -> WHILE_PAREN_CLOSE
        self._add_state_rule(FSMState.WHILE_PAREN_STATEMENT, TokenState.DO,
                             FSMState.WHILE_PAREN_CLOSE)
        # WHILE_PAREN_CLOSE -> BRACE_OPEN -> WHILE_BRACE_OPEN
        self._add_state_rule(FSMState.WHILE_PAREN_CLOSE, TokenState.BRACE_OPEN,
                             FSMState.WHILE_BRACE_OPEN)
        # WHILE_PAREN_CLOSE -> SEMICOLON -> WHILE_END
        self._add_state_rule(FSMState.WHILE_PAREN_CLOSE, TokenState.SEMICOLON,
                             FSMState.WHILE_END)
        # WHILE_PAREN_CLOSE -> STATEMENT -> WHILE_SINGLE_STATEMENT
        self._add_state_rule(FSMState.WHILE_PAREN_CLOSE, TokenState.STATEMENT,
                             FSMState.WHILE_SINGLE_STATEMENT)
        # WHILE_PAREN_CLOSE -> IF -> WHILE_SINGLE_STATEMENT
        self._add_state_rule(FSMState.WHILE_PAREN_CLOSE, TokenState.IF,
                             FSMState.WHILE_SINGLE_STATEMENT)
        # WHILE_PAREN_CLOSE -> WHILE -> WHILE_SINGLE_STATEMENT
        self._add_state_rule(FSMState.WHILE_PAREN_CLOSE, TokenState.WHILE,
                             FSMState.WHILE_SINGLE_STATEMENT)
        # WHILE_PAREN_CLOSE -> DO -> WHILE_SINGLE_STATEMENT
        self._add_state_rule(FSMState.WHILE_PAREN_CLOSE, TokenState.DO,
                             FSMState.WHILE_SINGLE_STATEMENT)
        # WHILE_PAREN_CLOSE -> FOR -> WHILE_SINGLE_STATEMENT
        self._add_state_rule(FSMState.WHILE_PAREN_CLOSE, TokenState.FOR,
                             FSMState.WHILE_SINGLE_STATEMENT)
        # WHILE_PAREN_CLOSE -> FUNCTION -> WHILE_SINGLE_STATEMENT
        self._add_state_rule(FSMState.WHILE_PAREN_CLOSE, TokenState.FUNCTION,
                             FSMState.WHILE_SINGLE_STATEMENT)
        # WHILE_SINGLE_STATEMENT -> LAMBDA -> WHILE_END
        self._add_state_rule(FSMState.WHILE_SINGLE_STATEMENT, TokenState.LAMBDA,
                             FSMState.WHILE_END)
        # WHILE_BRACE_OPEN -> BRACE_CLOSE -> WHILE_END
        self._add_state_rule(FSMState.WHILE_BRACE_OPEN, TokenState.BRACE_CLOSE,
                             FSMState.WHILE_END)
        # WHILE_BRACE_OPEN -> SEMICOLON -> WHILE_STATEMENT
        self._add_state_rule(FSMState.WHILE_BRACE_OPEN, TokenState.SEMICOLON,
                             FSMState.WHILE_STATEMENT)
        # WHILE_BRACE_OPEN -> STATEMENT -> WHILE_STATEMENT
        self._add_state_rule(FSMState.WHILE_BRACE_OPEN, TokenState.STATEMENT,
                             FSMState.WHILE_STATEMENT)
        # WHILE_BRACE_OPEN -> IF -> WHILE_STATEMENT
        self._add_state_rule(FSMState.WHILE_BRACE_OPEN, TokenState.IF,
                             FSMState.WHILE_STATEMENT)
        # WHILE_BRACE_OPEN -> WHILE -> WHILE_STATEMENT
        self._add_state_rule(FSMState.WHILE_BRACE_OPEN, TokenState.WHILE,
                             FSMState.WHILE_STATEMENT)
        # WHILE_BRACE_OPEN -> DO -> WHILE_STATEMENT
        self._add_state_rule(FSMState.WHILE_BRACE_OPEN, TokenState.DO,
                             FSMState.WHILE_STATEMENT)
        # WHILE_BRACE_OPEN -> FOR -> WHILE_STATEMENT
        self._add_state_rule(FSMState.WHILE_BRACE_OPEN, TokenState.FOR,
                             FSMState.WHILE_STATEMENT)
        # WHILE_BRACE_OPEN -> FUNCTION -> WHILE_STATEMENT
        self._add_state_rule(FSMState.WHILE_BRACE_OPEN, TokenState.FUNCTION,
                             FSMState.WHILE_STATEMENT)
        # WHILE_STATEMENT -> SEMICOLON -> WHILE_STATEMENT
        self._add_state_rule(FSMState.WHILE_STATEMENT, TokenState.SEMICOLON,
                             FSMState.WHILE_STATEMENT)
        # WHILE_STATEMENT -> STATEMENT -> WHILE_STATEMENT
        self._add_state_rule(FSMState.WHILE_STATEMENT, TokenState.STATEMENT,
                             FSMState.WHILE_STATEMENT)
        # WHILE_STATEMENT -> IF -> WHILE_STATEMENT
        self._add_state_rule(FSMState.WHILE_STATEMENT, TokenState.IF,
                             FSMState.WHILE_STATEMENT)
        # WHILE_STATEMENT -> WHILE -> WHILE_STATEMENT
        self._add_state_rule(FSMState.WHILE_STATEMENT, TokenState.WHILE,
                             FSMState.WHILE_STATEMENT)
        # WHILE_STATEMENT -> DO -> WHILE_STATEMENT
        self._add_state_rule(FSMState.WHILE_STATEMENT, TokenState.DO,
                             FSMState.WHILE_STATEMENT)
        # WHILE_STATEMENT -> FOR -> WHILE_STATEMENT
        self._add_state_rule(FSMState.WHILE_STATEMENT, TokenState.FOR,
                             FSMState.WHILE_STATEMENT)
        # WHILE_STATEMENT -> FUNCTION -> WHILE_STATEMENT
        self._add_state_rule(FSMState.WHILE_STATEMENT, TokenState.FUNCTION,
                             FSMState.WHILE_STATEMENT)
        # WHILE_STATEMENT -> BRACE_CLOSE -> WHILE_END
        self._add_state_rule(FSMState.WHILE_STATEMENT, TokenState.BRACE_CLOSE,
                             FSMState.WHILE_END)

    def init_do_while_states(self) -> None:
        """Init FSM states"""
        # DO_WHILE_START -> BRACE_OPEN -> DO_WHILE_BRACE_OPEN
        self._add_state_rule(FSMState.DO_WHILE_START, TokenState.BRACE_OPEN,
                             FSMState.DO_WHILE_BRACE_OPEN)
        # DO_WHILE_BRACE_OPEN -> BRACE_CLOSE -> DO_WHILE_BRACE_CLOSE
        self._add_state_rule(FSMState.DO_WHILE_BRACE_OPEN, TokenState.BRACE_CLOSE,
                             FSMState.DO_WHILE_BRACE_CLOSE)
        # DO_WHILE_BRACE_OPEN -> SEMICOLON -> DO_WHILE_STATEMENT
        self._add_state_rule(FSMState.DO_WHILE_BRACE_OPEN, TokenState.SEMICOLON,
                             FSMState.DO_WHILE_STATEMENT)
        # DO_WHILE_BRACE_OPEN -> BRACE_OPEN -> DO_WHILE_STATEMENT
        self._add_state_rule(FSMState.DO_WHILE_BRACE_OPEN, TokenState.STATEMENT,
                             FSMState.DO_WHILE_STATEMENT)
        # DO_WHILE_BRACE_OPEN -> IF -> DO_WHILE_STATEMENT
        self._add_state_rule(FSMState.DO_WHILE_BRACE_OPEN, TokenState.IF,
                             FSMState.DO_WHILE_STATEMENT)
        # DO_WHILE_BRACE_OPEN -> WHILE -> DO_WHILE_STATEMENT
        self._add_state_rule(FSMState.DO_WHILE_BRACE_OPEN, TokenState.WHILE,
                             FSMState.DO_WHILE_STATEMENT)
        # DO_WHILE_BRACE_OPEN -> DO -> DO_WHILE_STATEMENT
        self._add_state_rule(FSMState.DO_WHILE_BRACE_OPEN, TokenState.DO,
                             FSMState.DO_WHILE_STATEMENT)
        # DO_WHILE_BRACE_OPEN -> FOR -> DO_WHILE_STATEMENT
        self._add_state_rule(FSMState.DO_WHILE_BRACE_OPEN, TokenState.FOR,
                             FSMState.DO_WHILE_STATEMENT)
        # DO_WHILE_BRACE_OPEN -> FUNCTION -> DO_WHILE_STATEMENT
        self._add_state_rule(FSMState.DO_WHILE_BRACE_OPEN, TokenState.FUNCTION,
                             FSMState.DO_WHILE_STATEMENT)
        # DO_WHILE_STATEMENT -> SEMICOLON -> DO_WHILE_STATEMENT
        self._add_state_rule(FSMState.DO_WHILE_STATEMENT, TokenState.SEMICOLON,
                             FSMState.DO_WHILE_STATEMENT)
        # DO_WHILE_STATEMENT -> STATEMENT -> DO_WHILE_STATEMENT
        self._add_state_rule(FSMState.DO_WHILE_STATEMENT, TokenState.STATEMENT,
                             FSMState.DO_WHILE_STATEMENT)
        # DO_WHILE_STATEMENT -> IF -> DO_WHILE_STATEMENT
        self._add_state_rule(FSMState.DO_WHILE_STATEMENT, TokenState.IF,
                             FSMState.DO_WHILE_STATEMENT)
        # DO_WHILE_STATEMENT -> WHILE -> DO_WHILE_STATEMENT
        self._add_state_rule(FSMState.DO_WHILE_STATEMENT, TokenState.WHILE,
                             FSMState.DO_WHILE_STATEMENT)
        # DO_WHILE_STATEMENT -> DO -> DO_WHILE_STATEMENT
        self._add_state_rule(FSMState.DO_WHILE_STATEMENT, TokenState.DO,
                             FSMState.DO_WHILE_STATEMENT)
        # DO_WHILE_STATEMENT -> FOR -> DO_WHILE_STATEMENT
        self._add_state_rule(FSMState.DO_WHILE_STATEMENT, TokenState.FOR,
                             FSMState.DO_WHILE_STATEMENT)
        # DO_WHILE_STATEMENT -> FUNCTION -> DO_WHILE_STATEMENT
        self._add_state_rule(FSMState.DO_WHILE_STATEMENT, TokenState.FUNCTION,
                             FSMState.DO_WHILE_STATEMENT)
        # DO_WHILE_STATEMENT -> BRACE_CLOSE -> DO_WHILE_BRACE_CLOSE
        self._add_state_rule(FSMState.DO_WHILE_STATEMENT, TokenState.BRACE_CLOSE,
                             FSMState.DO_WHILE_BRACE_CLOSE)
        # DO_WHILE_BRACE_CLOSE -> WHILE -> DO_WHILE_KEYWORD
        self._add_state_rule(FSMState.DO_WHILE_BRACE_CLOSE, TokenState.WHILE,
                             FSMState.DO_WHILE_KEYWORD)
        # DO_WHILE_KEYWORD -> PAREN_OPEN -> DO_WHILE_PAREN_OPEN
        self._add_state_rule(FSMState.DO_WHILE_KEYWORD, TokenState.PAREN_OPEN,
                             FSMState.DO_WHILE_PAREN_OPEN)
        # DO_WHILE_PAREN_OPEN -> SEMICOLON -> DO_WHILE_PAREN_STATEMENT
        self._add_state_rule(FSMState.DO_WHILE_PAREN_OPEN, TokenState.SEMICOLON,
                             FSMState.DO_WHILE_PAREN_STATEMENT)
        # DO_WHILE_PAREN_OPEN -> STATEMENT -> DO_WHILE_PAREN_STATEMENT
        self._add_state_rule(FSMState.DO_WHILE_PAREN_OPEN, TokenState.STATEMENT,
                             FSMState.DO_WHILE_PAREN_STATEMENT)
        # DO_WHILE_PAREN_STATEMENT -> SEMICOLON -> DO_WHILE_PAREN_STATEMENT
        self._add_state_rule(FSMState.DO_WHILE_PAREN_STATEMENT, TokenState.SEMICOLON,
                             FSMState.DO_WHILE_PAREN_STATEMENT)
        # DO_WHILE_PAREN_STATEMENT -> STATEMENT -> DO_WHILE_PAREN_STATEMENT
        self._add_state_rule(FSMState.DO_WHILE_PAREN_STATEMENT, TokenState.STATEMENT,
                             FSMState.DO_WHILE_PAREN_STATEMENT)
        # DO_WHILE_PAREN_STATEMENT -> PAREN_CLOSE -> DO_WHILE_PAREN_CLOSE
        self._add_state_rule(FSMState.DO_WHILE_PAREN_STATEMENT,
                             TokenState.PAREN_CLOSE, FSMState.DO_WHILE_PAREN_CLOSE)
        # DO_WHILE_PAREN_CLOSE -> DO_WHILE_PAREN_STATEMENT -> DO_WHILE_END
        self._add_state_rule(FSMState.DO_WHILE_PAREN_CLOSE, TokenState.SEMICOLON,
                             FSMState.DO_WHILE_END)

    def init_if_states(self) -> None:
        """Init FSM states"""
        # PART 1 - IF_THEN

        # IF_START -> PAREN_OPEN -> IF_PAREN_OPEN
        self._add_state_rule(FSMState.IF_START, TokenState.PAREN_OPEN,
                             FSMState.IF_PAREN_OPEN)
        # IF_START -> SEMICOLON -> IF_THEN_END
        self._add_state_rule(FSMState.IF_START, TokenState.SEMICOLON,
                             FSMState.IF_THEN_END)
        # IF_PAREN_OPEN -> STATEMENT -> IF_PAREN_STATEMENT
        self._add_state_rule(FSMState.IF_PAREN_OPEN, TokenState.STATEMENT,
                             FSMState.IF_PAREN_STATEMENT)
        # IF_PAREN_STATEMENT -> STATEMENT -> IF_PAREN_STATEMENT
        self._add_state_rule(FSMState.IF_PAREN_STATEMENT, TokenState.STATEMENT,
                             FSMState.IF_PAREN_STATEMENT)
        # IF_PAREN_STATEMENT -> PAREN_CLOSE -> IF_PAREN_CLOSE
        self._add_state_rule(FSMState.IF_PAREN_STATEMENT, TokenState.PAREN_CLOSE,
                             FSMState.IF_PAREN_CLOSE)
        # IF_PAREN_CLOSE -> BRACE_OPEN -> IF_THEN_BRACE_OPEN
        self._add_state_rule(FSMState.IF_PAREN_CLOSE, TokenState.BRACE_OPEN,
                             FSMState.IF_THEN_BRACE_OPEN)
        # IF_PAREN_CLOSE -> SEMICOLON -> IF_THEN_END
        self._add_state_rule(FSMState.IF_PAREN_CLOSE, TokenState.SEMICOLON,
                             FSMState.IF_THEN_END)
        # IF_PAREN_CLOSE -> STATEMENT -> IF_THEN_SINGLE_STATEMENT
        self._add_state_rule(FSMState.IF_PAREN_CLOSE, TokenState.STATEMENT,
                             FSMState.IF_THEN_SINGLE_STATEMENT)
        # IF_PAREN_CLOSE -> IF -> IF_THEN_SINGLE_STATEMENT
        self._add_state_rule(FSMState.IF_PAREN_CLOSE, TokenState.IF,
                             FSMState.IF_THEN_SINGLE_STATEMENT)
        # IF_PAREN_CLOSE -> WHILE -> IF_THEN_SINGLE_STATEMENT
        self._add_state_rule(FSMState.IF_PAREN_CLOSE, TokenState.WHILE,
                             FSMState.IF_THEN_SINGLE_STATEMENT)
        # IF_PAREN_CLOSE -> DO -> IF_THEN_SINGLE_STATEMENT
        self._add_state_rule(FSMState.IF_PAREN_CLOSE, TokenState.DO,
                             FSMState.IF_THEN_SINGLE_STATEMENT)
        # IF_PAREN_CLOSE -> FOR -> IF_THEN_SINGLE_STATEMENT
        self._add_state_rule(FSMState.IF_PAREN_CLOSE, TokenState.FOR,
                             FSMState.IF_THEN_SINGLE_STATEMENT)
        # IF_PAREN_CLOSE -> FUNCTION -> IF_THEN_SINGLE_STATEMENT
        self._add_state_rule(FSMState.IF_PAREN_CLOSE, TokenState.FUNCTION,
                             FSMState.IF_THEN_SINGLE_STATEMENT)
        # IF_THEN_SINGLE_STATEMENT -> ELSE -> IF_ELSE
        self._add_state_rule(FSMState.IF_THEN_SINGLE_STATEMENT, TokenState.ELSE,
                             FSMState.IF_ELSE)
        # IF_PAREN_CLOSE -> BRACE_OPEN -> IF_THEN_BRACE_OPEN
        self._add_state_rule(FSMState.IF_PAREN_CLOSE, TokenState.BRACE_OPEN,
                             FSMState.IF_THEN_BRACE_OPEN)
        # IF_THEN_BRACE_OPEN -> BRACE_CLOSE -> IF_THEN_END
        self._add_state_rule(FSMState.IF_THEN_BRACE_OPEN, TokenState.BRACE_CLOSE,
                             FSMState.IF_THEN_END)
        # IF_THEN_BRACE_OPEN -> SEMICOLON -> IF_THEN_STATEMENT
        self._add_state_rule(FSMState.IF_THEN_BRACE_OPEN, TokenState.SEMICOLON,
                             FSMState.IF_THEN_STATEMENT)
        # IF_THEN_BRACE_OPEN -> STATEMENT -> IF_THEN_STATEMENT
        self._add_state_rule(FSMState.IF_THEN_BRACE_OPEN, TokenState.STATEMENT,
                             FSMState.IF_THEN_STATEMENT)
        # IF_THEN_BRACE_OPEN -> IF -> IF_THEN_STATEMENT
        self._add_state_rule(FSMState.IF_THEN_BRACE_OPEN, TokenState.IF,
                             FSMState.IF_THEN_STATEMENT)
        # IF_THEN_BRACE_OPEN -> WHILE -> IF_THEN_STATEMENT
        self._add_state_rule(FSMState.IF_THEN_BRACE_OPEN, TokenState.WHILE,
                             FSMState.IF_THEN_STATEMENT)
        # IF_THEN_BRACE_OPEN -> DO -> IF_THEN_STATEMENT
        self._add_state_rule(FSMState.IF_THEN_BRACE_OPEN, TokenState.DO,
                             FSMState.IF_THEN_STATEMENT)
        # IF_THEN_BRACE_OPEN -> FOR -> IF_THEN_STATEMENT
        self._add_state_rule(FSMState.IF_THEN_BRACE_OPEN, TokenState.FOR,
                             FSMState.IF_THEN_STATEMENT)
        # IF_THEN_BRACE_OPEN -> FUNCTION -> IF_THEN_STATEMENT
        self._add_state_rule(FSMState.IF_THEN_BRACE_OPEN, TokenState.FUNCTION,
                             FSMState.IF_THEN_STATEMENT)
        # IF_THEN_STATEMENT -> SEMICOLON -> IF_THEN_STATEMENT
        self._add_state_rule(FSMState.IF_THEN_STATEMENT, TokenState.SEMICOLON,
                             FSMState.IF_THEN_STATEMENT)
        # IF_THEN_STATEMENT -> STATEMENT -> IF_THEN_STATEMENT
        self._add_state_rule(FSMState.IF_THEN_STATEMENT, TokenState.STATEMENT,
                             FSMState.IF_THEN_STATEMENT)
        # IF_THEN_STATEMENT -> IF -> IF_THEN_STATEMENT
        self._add_state_rule(FSMState.IF_THEN_STATEMENT, TokenState.IF,
                             FSMState.IF_THEN_STATEMENT)
        # IF_THEN_STATEMENT -> WHILE -> IF_THEN_STATEMENT
        self._add_state_rule(FSMState.IF_THEN_STATEMENT, TokenState.WHILE,
                             FSMState.IF_THEN_STATEMENT)
        # IF_THEN_STATEMENT -> DO -> IF_THEN_STATEMENT
        self._add_state_rule(FSMState.IF_THEN_STATEMENT, TokenState.DO,
                             FSMState.IF_THEN_STATEMENT)
        # IF_THEN_STATEMENT -> FOR -> IF_THEN_STATEMENT
        self._add_state_rule(FSMState.IF_THEN_STATEMENT, TokenState.FOR,
                             FSMState.IF_THEN_STATEMENT)
        # IF_THEN_STATEMENT -> FUNCTION -> IF_THEN_STATEMENT
        self._add_state_rule(FSMState.IF_THEN_STATEMENT, TokenState.FUNCTION,
                             FSMState.IF_THEN_STATEMENT)
        # IF_THEN_STATEMENT -> BRACE_CLOSE -> IF_THEN_END
        self._add_state_rule(FSMState.IF_THEN_STATEMENT, TokenState.BRACE_CLOSE,
                             FSMState.IF_THEN_END)

        # Part 2 - ELSE_IF

        # IF_ELSE -> IF -> ELSE_IF_STATEMENT
        self._add_state_rule(FSMState.IF_ELSE, TokenState.IF,
                             FSMState.ELSE_IF_STATEMENT)
        # ELSE_IF_STATEMENT -> LAMBDA -> ELSE_IF_END
        self._add_state_rule(FSMState.ELSE_IF_STATEMENT, TokenState.LAMBDA,
                             FSMState.ELSE_IF_END)
        # ELSE_IF_END -> ELSE -> IF_ELSE
        self._add_state_rule(FSMState.ELSE_IF_STATEMENT, TokenState.ELSE,
                             FSMState.IF_ELSE)

        # PART 3 - IF_ELSE

        # IF_THEN_END -> ELSE -> IF_ELSE
        self._add_state_rule(FSMState.IF_THEN_END, TokenState.ELSE,
                             FSMState.IF_ELSE)
        # IF_ELSE -> SEMICOLON -> IF_ELSE_END
        self._add_state_rule(FSMState.IF_ELSE, TokenState.SEMICOLON,
                             FSMState.IF_ELSE_END)
        # IF_ELSE -> STATEMENT -> IF_ELSE_SINGLE_STATEMENT
        self._add_state_rule(FSMState.IF_ELSE, TokenState.STATEMENT,
                             FSMState.IF_ELSE_SINGLE_STATEMENT)
        # IF_ELSE -> WHILE -> IF_ELSE_SINGLE_STATEMENT
        self._add_state_rule(FSMState.IF_ELSE, TokenState.WHILE,
                             FSMState.IF_ELSE_SINGLE_STATEMENT)
        # IF_ELSE -> DO -> IF_ELSE_SINGLE_STATEMENT
        self._add_state_rule(FSMState.IF_ELSE, TokenState.DO,
                             FSMState.IF_ELSE_SINGLE_STATEMENT)
        # IF_ELSE -> FOR -> IF_ELSE_SINGLE_STATEMENT
        self._add_state_rule(FSMState.IF_ELSE, TokenState.FOR,
                             FSMState.IF_ELSE_SINGLE_STATEMENT)
        # IF_ELSE -> FUNCTION -> IF_ELSE_SINGLE_STATEMENT
        self._add_state_rule(FSMState.IF_ELSE, TokenState.FUNCTION,
                             FSMState.IF_ELSE_SINGLE_STATEMENT)
        # IF_ELSE_SINGLE_STATEMENT -> LAMBDA -> IF_ELSE_END
        self._add_state_rule(FSMState.IF_ELSE_SINGLE_STATEMENT, TokenState.LAMBDA,
                             FSMState.IF_ELSE_END)
        # IF_ELSE -> BRACE_OPEN -> IF_ELSE_BRACE_OPEN
        self._add_state_rule(FSMState.IF_ELSE, TokenState.BRACE_OPEN,
                             FSMState.IF_ELSE_BRACE_OPEN)
        # IF_ELSE_BRACE_OPEN -> BRACE_CLOSE -> IF_ELSE_END
        self._add_state_rule(FSMState.IF_ELSE_BRACE_OPEN, TokenState.BRACE_CLOSE,
                             FSMState.IF_ELSE_END)
        # IF_ELSE_BRACE_OPEN -> SEMICOLON -> IF_ELSE_STATEMENT
        self._add_state_rule(FSMState.IF_ELSE_BRACE_OPEN, TokenState.SEMICOLON,
                             FSMState.IF_ELSE_STATEMENT)
        # IF_ELSE_BRACE_OPEN -> STATEMENT -> IF_ELSE_STATEMENT
        self._add_state_rule(FSMState.IF_ELSE_BRACE_OPEN, TokenState.STATEMENT,
                             FSMState.IF_ELSE_STATEMENT)
        # IF_ELSE_BRACE_OPEN -> IF -> IF_ELSE_STATEMENT
        self._add_state_rule(FSMState.IF_ELSE_BRACE_OPEN, TokenState.IF,
                             FSMState.IF_ELSE_STATEMENT)
        # IF_ELSE_BRACE_OPEN -> WHILE -> IF_ELSE_STATEMENT
        self._add_state_rule(FSMState.IF_ELSE_BRACE_OPEN, TokenState.WHILE,
                             FSMState.IF_ELSE_STATEMENT)
        # IF_ELSE_BRACE_OPEN -> DO -> IF_ELSE_STATEMENT
        self._add_state_rule(FSMState.IF_ELSE_BRACE_OPEN, TokenState.DO,
                             FSMState.IF_ELSE_STATEMENT)
        # IF_ELSE_BRACE_OPEN -> FOR -> IF_ELSE_STATEMENT
        self._add_state_rule(FSMState.IF_ELSE_BRACE_OPEN, TokenState.FOR,
                             FSMState.IF_ELSE_STATEMENT)
        # IF_ELSE_BRACE_OPEN -> FUNCTION -> IF_ELSE_STATEMENT
        self._add_state_rule(FSMState.IF_ELSE_BRACE_OPEN, TokenState.FUNCTION,
                             FSMState.IF_ELSE_STATEMENT)
        # IF_ELSE_STATEMENT -> SEMICOLON -> IF_ELSE_STATEMENT
        self._add_state_rule(FSMState.IF_ELSE_STATEMENT, TokenState.SEMICOLON,
                             FSMState.IF_ELSE_STATEMENT)
        # IF_ELSE_STATEMENT -> STATEMENT -> IF_ELSE_STATEMENT
        self._add_state_rule(FSMState.IF_ELSE_STATEMENT, TokenState.STATEMENT,
                             FSMState.IF_ELSE_STATEMENT)
        # IF_ELSE_STATEMENT -> IF -> IF_ELSE_STATEMENT
        self._add_state_rule(FSMState.IF_ELSE_STATEMENT, TokenState.IF,
                             FSMState.IF_ELSE_STATEMENT)
        # IF_ELSE_STATEMENT -> WHILE -> IF_ELSE_STATEMENT
        self._add_state_rule(FSMState.IF_ELSE_STATEMENT, TokenState.WHILE,
                             FSMState.IF_ELSE_STATEMENT)
        # IF_ELSE_STATEMENT -> DO -> IF_ELSE_STATEMENT
        self._add_state_rule(FSMState.IF_ELSE_STATEMENT, TokenState.DO,
                             FSMState.IF_ELSE_STATEMENT)
        # IF_ELSE_STATEMENT -> FOR -> IF_ELSE_STATEMENT
        self._add_state_rule(FSMState.IF_ELSE_STATEMENT, TokenState.FOR,
                             FSMState.IF_ELSE_STATEMENT)
        # IF_ELSE_STATEMENT -> FUNCTION -> IF_ELSE_STATEMENT
        self._add_state_rule(FSMState.IF_ELSE_STATEMENT, TokenState.FUNCTION,
                             FSMState.IF_ELSE_STATEMENT)
        # IF_ELSE_STATEMENT -> BRACE_CLOSE -> IF_ELSE_END
        self._add_state_rule(FSMState.IF_ELSE_STATEMENT, TokenState.BRACE_CLOSE,
                             FSMState.IF_ELSE_END)

    def init_for_states(self) -> None:
        """Init FSM states"""
        # FOR_START -> PAREN_OPEN -> FOR_PAREN_OPEN
        self._add_state_rule(FSMState.FOR_START, TokenState.PAREN_OPEN,
                             FSMState.FOR_PAREN_OPEN)
        # FOR_PAREN_OPEN -> SEMICOLON -> FOR_INIT_END
        self._add_state_rule(FSMState.FOR_PAREN_OPEN, TokenState.SEMICOLON,
                             FSMState.FOR_INIT_END)
        # FOR_PAREN_OPEN -> STATEMENT -> FOR_INIT
        self._add_state_rule(FSMState.FOR_PAREN_OPEN, TokenState.STATEMENT,
                             FSMState.FOR_INIT)
        # FOR_INIT -> SEMICOLON -> FOR_INIT_END
        self._add_state_rule(FSMState.FOR_INIT, TokenState.SEMICOLON,
                             FSMState.FOR_INIT_END)
        # FOR_INIT_END -> SEMICOLON -> FOR_COND_END
        self._add_state_rule(FSMState.FOR_INIT_END, TokenState.SEMICOLON,
                             FSMState.FOR_COND_END)
        # FOR_INIT_END -> STATEMENT -> FOR_COND
        self._add_state_rule(FSMState.FOR_INIT_END, TokenState.STATEMENT,
                             FSMState.FOR_COND)
        # FOR_COND -> SEMICOLON -> FOR_COND_END
        self._add_state_rule(FSMState.FOR_COND, TokenState.SEMICOLON,
                             FSMState.FOR_COND_END)
        # FOR_COND_END -> PAREN_CLOSE -> FOR_PAREN_CLOSE
        self._add_state_rule(FSMState.FOR_COND_END, TokenState.PAREN_CLOSE,
                             FSMState.FOR_PAREN_CLOSE)
        # FOR_COND_END -> STATEMENT -> FOR_MODIFY
        self._add_state_rule(FSMState.FOR_COND_END, TokenState.STATEMENT,
                             FSMState.FOR_MODIFY)
        # FOR_MODIFY -> PAREN_CLOSE -> FOR_PAREN_CLOSE
        self._add_state_rule(FSMState.FOR_MODIFY, TokenState.PAREN_CLOSE,
                             FSMState.FOR_PAREN_CLOSE)
        # FOR_PAREN_CLOSE -> SEMICOLON -> FOR_END
        self._add_state_rule(FSMState.FOR_PAREN_CLOSE, TokenState.SEMICOLON,
                             FSMState.FOR_END)
        # FOR_PAREN_CLOSE -> STATEMENT -> FOR_SINGLE_STATEMENT
        self._add_state_rule(FSMState.FOR_PAREN_CLOSE, TokenState.STATEMENT,
                             FSMState.FOR_SINGLE_STATEMENT)
        # FOR_PAREN_CLOSE -> IF -> FOR_SINGLE_STATEMENT
        self._add_state_rule(FSMState.FOR_PAREN_CLOSE, TokenState.IF,
                             FSMState.FOR_SINGLE_STATEMENT)
        # FOR_PAREN_CLOSE -> WHILE -> FOR_SINGLE_STATEMENT
        self._add_state_rule(FSMState.FOR_PAREN_CLOSE, TokenState.WHILE,
                             FSMState.FOR_SINGLE_STATEMENT)
        # FOR_PAREN_CLOSE -> DO -> FOR_SINGLE_STATEMENT
        self._add_state_rule(FSMState.FOR_PAREN_CLOSE, TokenState.DO,
                             FSMState.FOR_SINGLE_STATEMENT)
        # FOR_PAREN_CLOSE -> FOR -> FOR_SINGLE_STATEMENT
        self._add_state_rule(FSMState.FOR_PAREN_CLOSE, TokenState.FOR,
                             FSMState.FOR_SINGLE_STATEMENT)
        # FOR_PAREN_CLOSE -> FUNCTION -> FOR_SINGLE_STATEMENT
        self._add_state_rule(FSMState.FOR_PAREN_CLOSE, TokenState.FUNCTION,
                             FSMState.FOR_SINGLE_STATEMENT)
        # FOR_SINGLE_STATEMENT -> LAMBDA -> FOR_END
        self._add_state_rule(FSMState.FOR_SINGLE_STATEMENT, TokenState.LAMBDA,
                             FSMState.FOR_END)
        # FOR_PAREN_CLOSE -> BRACE_OPEN -> FOR_BRACE_OPEN
        self._add_state_rule(FSMState.FOR_PAREN_CLOSE, TokenState.BRACE_OPEN,
                             FSMState.FOR_BRACE_OPEN)
        # FOR_BRACE_OPEN -> BRACE_CLOSE -> FOR_END
        self._add_state_rule(FSMState.FOR_BRACE_OPEN, TokenState.BRACE_CLOSE,
                             FSMState.FOR_END)
        # FOR_BRACE_OPEN -> SEMICOLON -> FOR_STATEMENT
        self._add_state_rule(FSMState.FOR_BRACE_OPEN, TokenState.SEMICOLON,
                             FSMState.FOR_STATEMENT)
        # FOR_BRACE_OPEN -> STATEMENT -> FOR_STATEMENT
        self._add_state_rule(FSMState.FOR_BRACE_OPEN, TokenState.STATEMENT,
                             FSMState.FOR_STATEMENT)
        # FOR_BRACE_OPEN -> IF -> FOR_STATEMENT
        self._add_state_rule(FSMState.FOR_BRACE_OPEN, TokenState.IF,
                             FSMState.FOR_STATEMENT)
        # FOR_BRACE_OPEN -> WHILE -> FOR_STATEMENT
        self._add_state_rule(FSMState.FOR_BRACE_OPEN, TokenState.WHILE,
                             FSMState.FOR_STATEMENT)
        # FOR_BRACE_OPEN -> DO -> FOR_STATEMENT
        self._add_state_rule(FSMState.FOR_BRACE_OPEN, TokenState.DO,
                             FSMState.FOR_STATEMENT)
        # FOR_BRACE_OPEN -> FOR -> FOR_STATEMENT
        self._add_state_rule(FSMState.FOR_BRACE_OPEN, TokenState.FOR,
                             FSMState.FOR_STATEMENT)
        # FOR_BRACE_OPEN -> FUNCTION -> FOR_STATEMENT
        self._add_state_rule(FSMState.FOR_BRACE_OPEN, TokenState.FUNCTION,
                             FSMState.FOR_STATEMENT)
        # FOR_STATEMENT -> SEMICOLON -> FOR_STATEMENT
        self._add_state_rule(FSMState.FOR_STATEMENT, TokenState.SEMICOLON,
                             FSMState.FOR_STATEMENT)
        # FOR_STATEMENT -> STATEMENT -> FOR_STATEMENT
        self._add_state_rule(FSMState.FOR_STATEMENT, TokenState.STATEMENT,
                             FSMState.FOR_STATEMENT)
        # FOR_STATEMENT -> IF -> FOR_STATEMENT
        self._add_state_rule(FSMState.FOR_STATEMENT, TokenState.IF,
                             FSMState.FOR_STATEMENT)
        # FOR_STATEMENT -> WHILE -> FOR_STATEMENT
        self._add_state_rule(FSMState.FOR_STATEMENT, TokenState.WHILE,
                             FSMState.FOR_STATEMENT)
        # FOR_STATEMENT -> DO -> FOR_STATEMENT
        self._add_state_rule(FSMState.FOR_STATEMENT, TokenState.DO,
                             FSMState.FOR_STATEMENT)
        # FOR_STATEMENT -> FOR -> FOR_STATEMENT
        self._add_state_rule(FSMState.FOR_STATEMENT, TokenState.FOR,
                             FSMState.FOR_STATEMENT)
        # FOR_STATEMENT -> FUNCTION -> FOR_STATEMENT
        self._add_state_rule(FSMState.FOR_STATEMENT, TokenState.FUNCTION,
                             FSMState.FOR_STATEMENT)
        # FOR_STATEMENT -> BRACE_CLOSE -> FOR_END
        self._add_state_rule(FSMState.FOR_STATEMENT, TokenState.BRACE_CLOSE,
                             FSMState.FOR_END)

    def init_function_states(self) -> None:
        """Init FSM states"""
        # FUNC_START -> BRACE_OPEN -> FUNC_BRACE_OPEN
        self._add_state_rule(FSMState.FUNC_START, TokenState.BRACE_OPEN,
                             FSMState.FUNC_BRACE_OPEN)
        # FUNC_START -> SEMICOLON -> FUNC_END
        self._add_state_rule(FSMState.FUNC_START, TokenState.SEMICOLON,
                             FSMState.FUNC_END)
        # FUNC_BRACE_OPEN -> BRACE_CLOSE -> FUNC_END
        self._add_state_rule(FSMState.FUNC_BRACE_OPEN, TokenState.BRACE_CLOSE,
                             FSMState.FUNC_END)
        # FUNC_BRACE_OPEN -> SEMICOLON -> FUNC_STATEMENT
        self._add_state_rule(FSMState.FUNC_BRACE_OPEN, TokenState.SEMICOLON,
                             FSMState.FUNC_STATEMENT)
        # FUNC_BRACE_OPEN -> STATEMENT -> FUNC_STATEMENT
        self._add_state_rule(FSMState.FUNC_BRACE_OPEN, TokenState.STATEMENT,
                             FSMState.FUNC_STATEMENT)
        # FUNC_BRACE_OPEN -> IF -> FUNC_STATEMENT
        self._add_state_rule(FSMState.FUNC_BRACE_OPEN, TokenState.IF,
                             FSMState.FUNC_STATEMENT)
        # FUNC_BRACE_OPEN -> WHILE -> FUNC_STATEMENT
        self._add_state_rule(FSMState.FUNC_BRACE_OPEN, TokenState.WHILE,
                             FSMState.FUNC_STATEMENT)
        # FUNC_BRACE_OPEN -> DO -> FUNC_STATEMENT
        self._add_state_rule(FSMState.FUNC_BRACE_OPEN, TokenState.DO,
                             FSMState.FUNC_STATEMENT)
        # FUNC_BRACE_OPEN -> FOR -> FUNC_STATEMENT
        self._add_state_rule(FSMState.FUNC_BRACE_OPEN, TokenState.FOR,
                             FSMState.FUNC_STATEMENT)
        # FUNC_BRACE_OPEN -> FUNCTION -> FUNC_STATEMENT
        self._add_state_rule(FSMState.FUNC_BRACE_OPEN, TokenState.FUNCTION,
                             FSMState.FUNC_STATEMENT)
        # FUNC_STATEMENT -> SEMICOLON -> FUNC_STATEMENT
        self._add_state_rule(FSMState.FUNC_STATEMENT, TokenState.SEMICOLON,
                             FSMState.FUNC_STATEMENT)
        # FUNC_STATEMENT -> STATEMENT -> FUNC_STATEMENT
        self._add_state_rule(FSMState.FUNC_STATEMENT, TokenState.STATEMENT,
                             FSMState.FUNC_STATEMENT)
        # FUNC_STATEMENT -> IF -> FUNC_STATEMENT
        self._add_state_rule(FSMState.FUNC_STATEMENT, TokenState.IF,
                             FSMState.FUNC_STATEMENT)
        # FUNC_STATEMENT -> WHILE -> FUNC_STATEMENT
        self._add_state_rule(FSMState.FUNC_STATEMENT, TokenState.WHILE,
                             FSMState.FUNC_STATEMENT)
        # FUNC_STATEMENT -> DO -> FUNC_STATEMENT
        self._add_state_rule(FSMState.FUNC_STATEMENT, TokenState.DO,
                             FSMState.FUNC_STATEMENT)
        # FUNC_STATEMENT -> FOR -> FUNC_STATEMENT
        self._add_state_rule(FSMState.FUNC_STATEMENT, TokenState.FOR,
                             FSMState.FUNC_STATEMENT)
        # FUNC_STATEMENT -> FUNCTION -> FUNC_STATEMENT
        self._add_state_rule(FSMState.FUNC_STATEMENT, TokenState.FUNCTION,
                             FSMState.FUNC_STATEMENT)
        # FUNC_STATEMENT -> BRACE_CLOSE -> FUNC_END
        self._add_state_rule(FSMState.FUNC_STATEMENT, TokenState.BRACE_CLOSE,
                             FSMState.FUNC_END)

    def _add_state_rule(self, start_state: FSMState, token_state_input: TokenState,
                        end_state: FSMState) -> None:
        self.states[start_state.value][token_state_input.value] = end_state

    def _map_FSM_to_Decomp(self, state: FSMState) -> DecompStates:
        if FSMState.STATEMENT_START <= state <= FSMState.STATEMENT_END:
            return DecompStates.P1

        if FSMState.IF_START <= state <= FSMState.IF_ELSE_END:
            if state == FSMState.IF_START:
                return DecompStates.D0
            if FSMState.IF_START < state <= FSMState.IF_THEN_END:
                return DecompStates.D0_END
            if state == FSMState.IF_ELSE:
                return DecompStates.D1
            return DecompStates.D1_END

        if FSMState.WHILE_START <= state <= FSMState.WHILE_END:
            if state == FSMState.WHILE_START:
                return DecompStates.D2
            return DecompStates.D2_END

        if FSMState.DO_WHILE_START <= state <= FSMState.DO_WHILE_END:
            if state == FSMState.DO_WHILE_START:
                return DecompStates.D3
            return DecompStates.D3_END

        if FSMState.FOR_START <= state <= FSMState.FOR_END:
            if FSMState.FOR_START <= state <= FSMState.FOR_INIT_END:
                return DecompStates.P1
            if FSMState.FOR_COND <= state <= FSMState.FOR_COND_END:
                return DecompStates.D0
            return DecompStates.D0_END

        if FSMState.FUNC_START <= state <= FSMState.FUNC_END:
            if state == FSMState.FUNC_START:
                return DecompStates.F1
            return DecompStates.F1_END

    def is_fsm_start_state(self, state: FSMState) -> bool:
        """Init if state is FSM start state"""
        return state == FSMState.STATEMENT_START \
            or state == FSMState.IF_START \
            or state == FSMState.WHILE_START \
            or state == FSMState.DO_WHILE_START \
            or state == FSMState.FOR_START \
            or state == FSMState.FUNC_START

    def add_string(self, string: str) -> None:
        """Add string to parser"""
        self.strings.append(string)

    def parse(self) -> Node:
        """Parse strings with tokenizer"""
        try:
            for i, string in enumerate(self.strings):
                self.tokenizer.tokenize(string, i+1)
                self.tokens += self.tokenizer.tokens

            return self.parse_tokens(self.tokens)
        except TokenizerError as tokenizer_error:
            print(tokenizer_error)

    def parse_tokens(self, tokens: Deque[Token]) -> Node:
        """Parse tokens into tree Nodes"""
        root = Node(-1)
        walker = root

        while tokens:
            peek_token = tokens[0]
            re_node = self.build_tree(walker, tokens)
            walker = re_node if re_node else walker

            if tokens and peek_token == tokens[0]:
                tokens.popleft()

        if root.children:
            if root.children[0].parents:
                root.children[0].parents.pop(0)
            return root.children[0]
        return root

    def build_tree(self, root: Node, tokens: Deque[Token], state=None) -> Node:
        """Entry point to decide which start tree to build"""
        if not state:
            peek_token = tokens[0]
            peek_input = peek_token.type
            state = self.states[FSMState.INIT_START.value][peek_input.value]

        if not self.is_fsm_start_state(state):
            return

        if state == FSMState.STATEMENT_START:
            return self.build_statement_tree(root, tokens)
        if state == FSMState.IF_START:
            return self.build_if_tree(root, tokens)
        if state == FSMState.WHILE_START:
            return self.build_while_tree(root, tokens)
        if state == FSMState.DO_WHILE_START:
            return self.build_do_while_tree(root, tokens)
        if state == FSMState.FOR_START:
            return self.build_for_tree(root, tokens)
        if state == FSMState.FUNC_START:
            return self.build_function_tree(root, tokens)

    def build_statement_tree(self, root: Node, tokens: Deque[Token]) -> Node:
        """Build statement tree type"""
        if not root:
            return root

        token = tokens.popleft()
        token_input = token.type
        state = self.states[FSMState.INIT_START.value][token_input.value]

        if state != FSMState.STATEMENT_START:
            return root

        walker = root

        if walker.type != DecompStates.P1:
            start_node = Node(walker.val+1, token)
            start_node.type = self._map_FSM_to_Decomp(state)
            start_node.parents.append(walker)
            walker.children.append(start_node)
            self.nodes.append(start_node)

            walker = start_node
        else:
            walker.tokens.append(token)

        while tokens:
            peek_token = tokens[0]
            peek_input = peek_token.type
            peek_state = self.states[state.value][peek_input.value]

            if peek_state == FSMState.ERROR:
                print("Error parsing token grammar for " + peek_token)
                return walker

            token = tokens.popleft()
            walker.tokens.append(token)

            if peek_state == FSMState.STATEMENT_END:
                break

            state = peek_state

        return walker

    def build_if_tree(self, root: Node, tokens: Deque[Token]) -> Node:
        """Build if-then-else tree type"""
        if not root:
            return root

        token = tokens.popleft()
        token_input = token.type
        state = self.states[FSMState.INIT_START.value][token_input.value]

        if state != FSMState.IF_START:
            return root

        start_node = Node(root.val+1)
        start_node.tokens.append(token)
        start_node.type = self._map_FSM_to_Decomp(state)
        start_node.parents.append(root)
        root.children.append(start_node)
        self.nodes.append(start_node)

        walker = start_node
        last_walkers: List[Node] = []
        end_node = None

        is_success = False

        while tokens:
            peek_token = tokens[0]
            peek_input = peek_token.type
            peek_state = self.states[state.value][peek_input.value]

            if peek_state == FSMState.ERROR:
                if is_success:
                    break

                print("Error parsing token grammar for " + peek_token)
                return walker

            if peek_state == FSMState.IF_THEN_SINGLE_STATEMENT \
                    or peek_state == FSMState.ELSE_IF_STATEMENT \
                    or peek_state == FSMState.IF_ELSE_SINGLE_STATEMENT:
                walker = self.build_tree(walker, tokens, None)

                last_walker = Node(walker.val+1)
                last_walker.tokens.append(walker.tokens[-1])
                last_walker.type = self._map_FSM_to_Decomp(peek_state)
                last_walker.parents.append(walker)
                walker.children.append(last_walker)
                last_walkers.append(last_walker)
                self.nodes.append(last_walker)

                walker = last_walker

                is_success = True

            elif peek_state == FSMState.IF_THEN_STATEMENT \
                    or peek_state == FSMState.IF_ELSE_STATEMENT:
                walker = self.build_tree(walker, tokens, None)

            elif peek_state == FSMState.IF_ELSE:
                token = tokens.popleft()

                new_node = Node(walker.val+1)
                new_node.tokens.append(token)
                new_node.parents.append(start_node)
                start_node.children.append(new_node)
                self.nodes.append(new_node)

                walker = new_node

                # In else branch, IF node is no longer D0 but D1
                start_node.type = DecompStates.D1

            elif peek_state == FSMState.IF_THEN_END \
                    or peek_state == FSMState.ELSE_IF_END \
                    or peek_state == FSMState.IF_ELSE_END:

                # If peek_state is END but state from pevious is BRACE_OPEN
                # then there is empty body {}; create empty body node
                if state == FSMState.IF_THEN_BRACE_OPEN\
                        or state == FSMState.IF_ELSE_BRACE_OPEN:
                    empty_node = Node(walker.val+1)
                    empty_token = Token(
                        walker.tokens[-1].line, DecompStates.P1, "")
                    empty_node.tokens.append(empty_token)
                    empty_node.type = DecompStates.P1
                    empty_node.parents.append(walker)
                    walker.children.append(empty_node)
                    self.nodes.append(empty_node)

                    walker = empty_node

                token = tokens.popleft()

                last_walker = Node(walker.val+1)
                last_walker.tokens.append(token)
                last_walker.type = self._map_FSM_to_Decomp(peek_state)
                last_walker.parents.append(walker)
                walker.children.append(last_walker)
                last_walkers.append(last_walker)
                self.nodes.append(last_walker)

                walker = last_walker

                is_success = True

            else:
                token = tokens.popleft()
                walker.tokens.append(token)

            state = peek_state

        # Finalize CFG structure

        # Create end_node
        end_node = Node(walker.val+1)
        end_node.tokens.append(walker.tokens[-1])
        end_node.type = self._map_FSM_to_Decomp(state)
        self.nodes.append(end_node)

        # Connect to start walker if it does not have more than two children
        if len(start_node.children) < 2:
            end_node.parents.append(start_node)
            start_node.children.append(end_node)

        # Connect previous last walkers
        for last_walker in last_walkers:
            end_node.parents.append(last_walker)
            last_walker.children.append(end_node)

        return end_node

    def build_while_tree(self, root: Node, tokens: Deque[Token]):
        """Build while loop tree type"""
        if not root:
            return root

        token = tokens.popleft()
        token_input = token.type
        state = self.states[FSMState.INIT_START.value][token_input.value]

        if state != FSMState.WHILE_START:
            return root

        start_node = Node(root.val+1)
        start_node.tokens.append(token)
        start_node.type = self._map_FSM_to_Decomp(state)
        start_node.parents.append(root)
        root.children.append(start_node)
        self.nodes.append(start_node)

        walker = start_node
        end_node = None

        is_success = False

        while tokens:
            peek_token = tokens[0]
            peek_input = peek_token.type
            peek_state = self.states[state.value][peek_input.value]

            if peek_state == FSMState.ERROR:
                if is_success:
                    break

                print("Error parsing token grammar for " + peek_token)
                return walker

            if peek_state == FSMState.WHILE_STATEMENT \
                    or peek_state == FSMState.WHILE_SINGLE_STATEMENT:
                walker = self.build_tree(walker, tokens, None)

                if peek_state == FSMState.WHILE_SINGLE_STATEMENT:
                    is_success = True
                    break

            elif peek_state == FSMState.WHILE_END:

                # If peek_state is END but state from pevious is BRACE_OPEN
                # then there is empty body {}; create empty body node
                if state == FSMState.WHILE_BRACE_OPEN:
                    empty_node = Node(walker.val+1)
                    empty_token = Token(
                        walker.tokens[-1].line, DecompStates.P1, "")
                    empty_node.tokens.append(empty_token)
                    empty_node.type = DecompStates.P1
                    empty_node.parents.append(walker)
                    walker.children.append(empty_node)
                    self.nodes.append(empty_node)

                    walker = empty_node

                token = tokens.popleft()

                end_node = Node(walker.val+1)
                end_node.tokens.append(token)
                end_node.type = self._map_FSM_to_Decomp(peek_state)
                self.nodes.append(end_node)

                is_success = True

            else:
                token = tokens.popleft()
                walker.tokens.append(token)

            state = peek_state

        # Finalize CFG structure

        # Link walker to start node
        walker.children.append(start_node)
        start_node.parents.append(walker)

        # Create end node if it does not exist using last token
        if not end_node:
            end_node = Node(walker.val+1)
            end_node.tokens.append(walker.tokens[-1])
            end_node.type = self._map_FSM_to_Decomp(state)
            self.nodes.append(end_node)

        # Link start node to end node
        end_node.parents.append(start_node)
        start_node.children.append(end_node)

        return end_node

    def build_do_while_tree(self, root: Node, tokens: Deque[Token]):
        """Build do while loop tree type"""
        if not root:
            return root

        token = tokens.popleft()
        token_input = token.type
        state = self.states[FSMState.INIT_START.value][token_input.value]

        if state != FSMState.DO_WHILE_START:
            return root

        start_node = Node(root.val+1)
        start_node.tokens.append(token)
        start_node.type = self._map_FSM_to_Decomp(state)
        start_node.parents.append(root)
        root.children.append(start_node)
        self.nodes.append(start_node)

        walker = start_node
        end_node = None

        is_success = False

        while tokens:
            peek_token = tokens[0]
            peek_input = peek_token.type
            peek_state = self.states[state.value][peek_input.value]

            if peek_state == FSMState.ERROR:
                if is_success:
                    break

                print("Error parsing token grammar for " + peek_token)
                return walker

            if peek_state == FSMState.DO_WHILE_STATEMENT:
                walker = self.build_tree(walker, tokens, None)

            elif peek_state == FSMState.DO_WHILE_END:
                token = tokens.popleft()
                walker.tokens.append(token)
                end_node = walker

                is_success = True
                break

            elif peek_state == FSMState.DO_WHILE_BRACE_CLOSE \
                    and state == FSMState.DO_WHILE_BRACE_OPEN:
                token = tokens.popleft()

                # If peek_state is END but state from pevious is BRACE_OPEN
                # then there is empty body {}; create empty body node
                empty_node = Node(walker.val+1)
                empty_node.tokens.append(token)
                empty_node.type = DecompStates.P1
                empty_node.parents.append(walker)
                walker.children.append(empty_node)
                self.nodes.append(empty_node)

                walker = empty_node

            elif peek_state == FSMState.DO_WHILE_KEYWORD:
                token = tokens.popleft()

                new_node = Node(walker.val+1)
                new_node.tokens.append(token)
                new_node.parents.append(walker)
                walker.children.append(new_node)
                self.nodes.append(new_node)

                walker = new_node

            else:
                token = tokens.popleft()
                walker.tokens.append(token)

            state = peek_state

        # Error check
        if not end_node or end_node == start_node:
            print("Error parsing token grammar for " + token)
            return walker

        # Finalize CFG structure

        # Link end node to start node
        end_node.type = self._map_FSM_to_Decomp(state)
        end_node.children.append(start_node)
        start_node.parents.append(end_node)

        return end_node

    def build_for_tree(self, root: Node, tokens: Deque[Token]):
        """Build for loop tree type"""
        if not root:
            return root

        token = tokens.popleft()
        token_input = token.type
        state = self.states[FSMState.INIT_START.value][token_input.value]

        if state != FSMState.FOR_START:
            return root

        start_node = Node(root.val+1)
        start_node.tokens.append(token)
        start_node.type = self._map_FSM_to_Decomp(state)
        start_node.parents.append(root)
        root.children.append(start_node)
        self.nodes.append(start_node)

        walker = start_node
        end_node = None
        for_cond: Node = None
        for_body_last_walker: Node = None
        for_modify: Node = None

        is_success = False

        while tokens:
            peek_token = tokens[0]
            peek_input = peek_token.type
            peek_state = self.states[state.value][peek_input.value]

            if peek_state == FSMState.ERROR:
                if is_success:
                    break

                print("Error parsing token grammar for " + peek_token)
                return walker

            if peek_state == FSMState.FOR_COND \
                    or peek_state == FSMState.FOR_COND_END:
                token = tokens.popleft()

                if not for_cond:
                    for_cond = Node(walker.val+1)
                    for_cond.tokens.append(token)
                    for_cond.type = self._map_FSM_to_Decomp(peek_state)
                    for_cond.parents.append(start_node)
                    start_node.children.append(for_cond)
                    self.nodes.append(for_cond)

                    walker = for_cond
                else:
                    walker.tokens.append(token)

            elif peek_state == FSMState.FOR_MODIFY \
                    or peek_state == FSMState.FOR_PAREN_CLOSE:
                token = tokens.popleft()

                if not for_modify:
                    for_modify = Node(walker.val+1)
                    for_modify.tokens.append(token)

                    # Link for_modify to for_cond
                    for_modify.children.append(for_cond)
                    for_cond.parents.append(for_modify)

                    self.nodes.append(for_modify)

                    walker = for_modify
                else:
                    walker.tokens.append(token)

            elif peek_state == FSMState.FOR_STATEMENT \
                    or peek_state == FSMState.FOR_SINGLE_STATEMENT:
                # Store old value
                old_for_cond_val = for_cond.val

                for_cond.val = walker.val
                walker = self.build_tree(for_cond, tokens, None)

                # Restore old value
                for_cond.val = old_for_cond_val

                for_body_last_walker = walker

                if peek_state == FSMState.FOR_SINGLE_STATEMENT:
                    is_success = True
                    break

            elif peek_state == FSMState.FOR_END:

                # If peekState is END but state from pevious is BRACE_OPEN
                # then there is empty body {}; create empty body node\
                if state == FSMState.FOR_BRACE_OPEN:
                    empty_node = Node(walker.val+1)
                    empty_token = Token(
                        walker.tokens[-1].line, DecompStates.P1, "")
                    empty_node.tokens.append(empty_token)
                    empty_node.type = DecompStates.P1

                    empty_node.parents.append(for_cond)
                    for_cond.children.append(empty_node)
                    self.nodes.append(empty_node)

                    for_body_last_walker = empty_node

                    walker = empty_node

                token = tokens.popleft()
                end_node = Node(walker.val+1)
                end_node.tokens.append(token)
                end_node.type = self._map_FSM_to_Decomp(peek_state)
                self.nodes.append(end_node)

                break

            else:
                token = tokens.popleft()
                walker.tokens.append(token)

            state = peek_state

        # Error check
        if not for_cond or not for_modify:
            print("Error parsing token grammar for " + token)
            return walker

        # Finalize CFG structure

        # Create end_node if it doesn't exist
        if not end_node:
            end_node = Node(walker.val+1)
            end_node.tokens.append(walker.tokens[-1])
            end_node.type = self._map_FSM_to_Decomp(state)
            self.nodes.append(end_node)

        # Link for_cond to end_node
        for_cond.children.append(end_node)
        end_node.parents.append(for_cond)

        # If for_body_last_walker exists, link for_body_last_walker to for_modify
        if for_body_last_walker:
            for_body_last_walker.children.append(for_modify)
            for_modify.parents.append(for_body_last_walker)
        else:
            for_cond.children.append(for_modify)
            for_modify.parents.append(for_cond)

        return end_node

    def build_function_tree(self, root: Node, tokens: Deque[Token]):
        """Build function tree type"""
        if not root:
            return root

        token = tokens.popleft()
        token_input = token.type
        state = self.states[FSMState.INIT_START.value][token_input.value]

        if state != FSMState.FUNC_START:
            return root

        start_node = Node(root.val+1)
        start_node.tokens.append(token)
        start_node.type = self._map_FSM_to_Decomp(state)
        start_node.parents.append(root)
        root.children.append(start_node)
        self.nodes.append(start_node)

        walker = start_node
        end_node = None

        is_success = False

        while tokens:
            peek_token = tokens[0]
            peek_input = peek_token.type
            peek_state = self.states[state.value][peek_input.value]

            if peek_state == FSMState.ERROR:
                if is_success:
                    break

                print("Error parsing token grammar for " + peek_token)
                return walker

            if peek_state == FSMState.FUNC_STATEMENT:
                walker = self.build_tree(walker, tokens, None)

            elif peek_state == FSMState.FUNC_END:

                if state == FSMState.FUNC_BRACE_OPEN:
                    empty_node = Node(walker.val+1)
                    empty_token = Token(
                        walker.tokens[-1].line, DecompStates.P1, "")
                    empty_node.tokens.append(empty_token)
                    empty_node.type = DecompStates.P1
                    empty_node.parents.append(walker)
                    walker.children.append(empty_node)
                    self.nodes.append(empty_node)

                    walker = empty_node

                token = tokens.popleft()

                # If function is a statement, ie ends in a SEMICOLOn like x = get();
                # Then change type to STATEMENT
                # And merge it with start_node
                if token.type == TokenState.SEMICOLON:
                    start_node.type = DecompStates.P1
                    start_node.tokens.append(token)
                    end_node = start_node
                else:
                    end_node = Node(walker.val+1)
                    end_node.tokens.append(token)
                    end_node.type = self._map_FSM_to_Decomp(peek_state)
                    end_node.parents.append(walker)
                    walker.children.append(end_node)
                    self.nodes.append(end_node)

                is_success = True
                break

            else:
                token = tokens.popleft()
                walker.tokens.append(token)

            state = peek_state

        if not end_node:
            print("Error parsing token grammar for " + peek_token)
            return walker

        return end_node
