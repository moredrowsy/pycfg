"""
Control Flow Graph
"""
from collections import defaultdict, deque
from typing import List
import matplotlib.pyplot as plt
import networkx as nx
from .node import Node
from .parser import Parser


class ControlFlowGraph():
    """Control Flow Graph"""

    def __init__(self) -> None:
        self.parser = Parser()
        self.nodes = []
        self.edges = []

    def add_string(self, string: str):
        """Add string to parser"""
        self.parser.add_string(string)

    def parse(self):
        """Call parser to parse all string inputs"""
        self.parser.parse()
        self.nodes = self.parser.nodes
        self.minimize_nodes(self.nodes)
        self.edges = self.get_edges_from_nodes(self.nodes)

    def minimize_nodes(self, node_list: List[Node]):
        """
        Merge nodes that are the same. Will relink all parent and children nodes
        """
        node_map = defaultdict(deque)
        for node in node_list:
            node_type = node.type.name if node.type else "None"
            line = node.tokens[0].line if node.tokens else "-1"
            node_map[f"T:{node_type} L:{line}"].append(
                node)

        for nodes in node_map.values():
            if len(nodes) < 2:
                continue

            root = nodes.popleft()

            # prepare root parents map
            root_parents = {}
            for parent in root.parents:
                root_parents[parent] = parent

            # prepare root children map
            root_children = {}
            for children in root.children:
                root_children[children] = children

            # merge parent nodes
            for node in nodes:
                # merge parents
                for parent in node.parents:
                    if parent is not root and parent not in root_parents:
                        # Add parent to root's parent
                        root.parents.append(parent)

                        # Add root to parent's child
                        parent.children.append(root)

                        # Remove node from parent's children
                        parent.children.remove(node)

                # merge children
                for child in node.children:
                    if child is not root and child not in root_children:
                        # Add children to root's children
                        root.children.append(child)

                        # Add root to childrne's parent
                        child.parents.append(root)

                        # Remove node from children's parents
                        child.parents.remove(node)

                node_list.remove(node)
                root.children.remove(node)

    def get_edges_from_nodes(self, nodes: List[Node]):
        """Produce a list of edge tuple from node list"""
        edges = []

        for node in nodes:
            for child in node.children:
                edges.append((node, child))

        return edges

    def graph(self):
        """
        Graph the CFG with the current nodes and edges
        Use this only after calling ControlFlowGraph.parse()
        """
        DG = nx.DiGraph()

        DG.add_nodes_from(self.nodes)  # Add nodes to graph
        DG.add_edges_from(self.edges)  # Add edges to graph

        # Get graph positions using Graphviz
        pos = nx.nx_agraph.graphviz_layout(DG)
        pos = nx.nx_agraph.graphviz_layout(DG, prog="dot")

        # Draw NetworkX's directed graph to Matplotlib
        nx.draw_networkx_nodes(DG, pos)
        nx.draw_networkx_labels(DG, pos)
        nx.draw_networkx_edges(DG, pos, edge_color='r', arrows=True)

        plt.show()
