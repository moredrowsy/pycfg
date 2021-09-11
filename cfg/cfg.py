"""
Control Flow Graph
"""
from collections import defaultdict, deque
from typing import List, Tuple
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

    def get_straight_and_curve_edges_from_edges(self, edges: List[Tuple[Node, Node]]):
        """
        Filter edges to straight and curve edges
        Curve edges are where e1 -> e2 and e2 -> e1
        """
        straight = []
        curve = []

        for edge in edges:
            e1, e2 = edge
            if (e2, e1) in edges:
                curve.append(edge)
            else:
                straight.append(edge)

        return straight, curve

    def print_nodes(self):
        """Prints a list of nodes"""
        output = "Nodes\n-----"

        if self.nodes:
            for node in self.nodes:
                output += f"\n{node}\n"
        else:
            output += "\nNone\n"

        print(output, end="")
        return output

    def print_edges(self):
        """Prints a list of edges"""
        output = "Edges\n-----\n"

        if self.edges:
            for edge in self.edges:
                output += f"({edge[0].val} --> {edge[1].val})\n"
        else:
            output += "None\n"

        print(output, end="")
        return output

    def draw_graph(self, title=None, filename=None):
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
        # nx.draw_networkx_edges(DG, pos, edge_color='r', arrows=True) # draw all edges

        # Get straight and curve edges
        straight, curve = self.get_straight_and_curve_edges_from_edges(
            self.edges)

        # draw straight edges
        nx.draw_networkx_edges(DG, pos, edgelist=straight, edge_color='r',
                               arrows=True)
        # draw curve edges
        nx.draw_networkx_edges(DG, pos, edgelist=curve,
                               connectionstyle=f"arc3, rad = {0.3}",
                               edge_color='r', arrows=True)

        if title:
            plt.title(title)

        if filename:
            plt.savefig(filename, format="PNG")

        plt.show()
