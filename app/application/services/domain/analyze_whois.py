from app.infrastructure.clients.whoisxml_client import get_whoisxml
import networkx as nx


async def analyze_whois(apex_domain: str):
    """WhoIs情報抽出を行う（whoisxml由来のノード/リレーションを構築）"""
    result = await get_whoisxml(apex_domain)
    # .com は上位、.jp 等は registryData 側に実データ。effective で吸収する。
    record = result.whois_record.effective

    G = nx.MultiDiGraph()

    G.add_node(apex_domain, type="domain")
    G.nodes[apex_domain]["created_date"] = record.created_date
    G.nodes[apex_domain]["updated_date"] = record.updated_date
    G.nodes[apex_domain]["expires_date"] = record.expires_date
    G.nodes[apex_domain]["status"] = record.status
    G.nodes[apex_domain]["estimated_domain_age"] = record.estimated_domain_age

    if record.registrar_name:
        G.add_node(record.registrar_name, type="registrar",iana_id=record.registrar_iana_id)
        G.add_edge(apex_domain, record.registrar_name, label="registered_with")

    if record.name_servers:
        for ns in record.name_servers.host_names:
            G.add_node(ns, type="name_server")
            G.add_edge(apex_domain, ns, label="name_server")

    if record.registrant:
        if record.registrant.organization:
            G.add_node(record.registrant.organization, type="organization")
            G.add_edge(apex_domain, record.registrant.organization, label="registrant_org")

        if record.registrant.country:
            G.add_node(record.registrant.country, type="country")
            G.add_edge(apex_domain, record.registrant.country, label="registrant_country")

        if record.registrant.email:
            G.add_node(record.registrant.email, type="email")
            G.add_edge(apex_domain, record.registrant.email, label="registrant_email")
            
    return G
