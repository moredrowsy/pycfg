"""
Control Flow Graph
"""
from .parser import Parser


class ControlFlowGraph():
    """Control Flow Graph"""

    def __init__(self) -> None:
        self.parser = Parser()

    def add_string(self, string: str):
        """Add string to parser"""
        self.parser.add_string(string)

    def parse(self):
        """Call parser to parse all string inputs"""
        root = self.parser.parse()
        nodes = self.parser.nodes
        print()

    def nodes(self):
        """Retrn a list of nodes"""
        return self.parser.nodes
