from app.infrastructure.request_models.holehe_model import HoleheResponseModel
from app.infrastructure.clients.holehe_client import check_email_service
import networkx as nx
from kg_gen.models import Graph

async def attribute_used_service(email: str) -> Graph:
  used_service: list[HoleheResponseModel] = await check_email_service(email)
  
  used_service_graph = nx.MultiDiGraph()
  used_service_graph.add_node(email, type = "email")
  
  for service in used_service:
    if service.exists:
      used_service_graph.add_node(service.name, type = "use_service")
      used_service_graph.add_edge(email, service.name, label = "use")
      
      if service.emailrecovery:
        used_service_graph.add_node(service.emailrecovery, type = "recoverymail")
        used_service_graph.add_edge(service.name, service.emailrecovery, label = "recovery email")
        
  return used_service_graph