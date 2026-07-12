import networkx as nx
from kg_gen.models import Graph

def generate_networkx(kg: Graph):
  G = nx.MultiDiGraph()

  G.add_nodes_from(kg.entities)

  G.add_edges_from((s, o, {"label": r}) for s, r, o in kg.relations)

  return G