import networkx as nx
from kg_gen.models import Graph

def generate_networkx(kg: set[tuple[str, str, str]]):
  G = nx.MultiDiGraph()
  
  add_edges = []
  
  for kg_tuple in kg:
    add_edges.append((kg_tuple[0], kg_tuple[2], {"label": kg_tuple[1]}))
  
  G.add_edges_from(add_edges)
  
  return G