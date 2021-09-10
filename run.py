"""
Run the control flow graph progarm
"""
from argparse import ArgumentParser
from pathlib import Path
from cfg import ControlFlowGraph


class Run():
    """
    Run Control Flow Graph
    """

    def start(self,):
        """Start"""
        cfg = ControlFlowGraph()

        filename = self.get_filename()

        with open(filename) as file:
            for line in file:
                cfg.add_string(line)

        cfg.parse()
        cfg.graph()

    def get_filename(self):
        """Get input filename"""
        parser = ArgumentParser()
        parser.add_argument('--file', help='File name')
        parser.add_argument('-f', help='File name')
        args = parser.parse_args()

        default = "input.txt"

        if not args.f or args.file:
            if Path(default).exists():
                return default
            return input("Enter filename:")

        return args.f if args.f else args.file


if __name__ == "__main__":
    Run().start()
