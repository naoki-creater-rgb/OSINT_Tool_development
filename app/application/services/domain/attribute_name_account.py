from app.infrastructure.clients.whatsmyname_client import check_user_service
import networkx as nx
from kg_gen.models import Graph

async def attribute_name_account(email: str) -> Graph:
  account_name = email.split("@")[0]
  
  use_service = await check_user_service(account_name)
  whatsmyname_G = nx.MultiDiGraph()
  
  whatsmyname_G.add_node(email, type = "email")
  
  for service in use_service:
    whatsmyname_G.add_node(service.site_name, type = "service name")
    whatsmyname_G.add_edge(email, service.site_name, label = "may use")
    
  return whatsmyname_G