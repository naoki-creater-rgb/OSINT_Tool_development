from app.infrastructure.clients.virustotal_client import virustotal_response
from app.infrastructure.clients.kg_gen_client import relation_generate_from_text, graph_from_tuples
from app.infrastructure.clients.networkx_client import generate_networkx
from kg_gen.models import Graph
import networkx as nx


async def analyze_virustotal(url: str):
    vt_result = await virustotal_response(url)
    attributes = vt_result.data.attributes
    stats = attributes.last_analysis_stats
    contexts = attributes.crowdsourced_context

    G = nx.MultiDiGraph()

    G.add_node(url, type="url")
    if stats:
        verdict = "malicious" if stats.malicious > 0 else "harmless"
        G.add_node(verdict, type="verdict")
        G.add_edge(url, verdict, label="verdict")

        # 悪性なら URLノードだけ色を変える
        if stats.malicious > 0:
            G.nodes[url]["color"] = "red"
            
    threats = set()
    for ctx in contexts:
        # --- B-1: 脅威（見出し title）ノード ---
        if ctx.title:
            threats.add(ctx.title)
            
    threats = list(set(threats))
    
    for threat in threats:
        G.add_node(threat, type="threat")
        G.add_edge(url, threat, label="has_threat")
        
    if contexts:
        ctx = contexts[0]
        if ctx.detail:
            ai_graph = relation_generate_from_text(ctx.detail)
            G_ai = generate_networkx(ai_graph)
            G = nx.compose(G, G_ai)
            
            anchor = ctx.title if ctx.title else url
            for node in G_ai.nodes():
                if G_ai.in_degree(node) == 0:
                    G.add_edge(anchor, node, label="analysis_detail")

    return G
