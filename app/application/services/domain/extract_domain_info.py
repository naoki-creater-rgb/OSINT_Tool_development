from app.infrastructure.clients.urlscanio_request_client import scan_url
from app.application.services.domain.analyze_virustotal import analyze_virustotal
from app.application.services.domain.analyze_whois import analyze_whois
from app.application.services.domain.extract_page_content import extract_page_content
from app.application.services.domain.extract_mail_info import extract_mail_info
from app.application.services.graph.prune import prune_graph
import networkx as nx

import asyncio


def _graph_or_empty(result, label: str) -> nx.MultiDiGraph:
    """gather(return_exceptions=True)の結果を安全にグラフ化する。

    サブフローが例外を投げても全体を巻き添えにせず、そのフローだけ空グラフ
    として握りつぶす（部分結果 > 全滅）。失敗はログに残す。
    """
    if isinstance(result, Exception):
        print(f"[!] {label} 失敗のためスキップ: {result!r}")
        return nx.MultiDiGraph()
    return result


async def extract_domain_info(url: str):
    """ドメイン情報抽出を行う（urlscan由来のノード/リレーションを構築）"""
    result = await scan_url(url)
    page = result.analysis.page
    requests = result.analysis.data.requests

    urlscan_G = nx.MultiDiGraph()

    domain = page.domain
    urlscan_G.add_node(domain, type="domain")
    
    if page.url:
        urlscan_G.add_node(page.url, type="url")
        urlscan_G.add_edge(domain, page.url, label="scanned_url")

    if page.apexDomain:
        urlscan_G.add_node(page.apexDomain, type="apex_domain")
        urlscan_G.add_edge(domain, page.apexDomain, label="apex_domain")

    if page.ip:
        urlscan_G.add_node(page.ip, type="ip")
        urlscan_G.add_edge(domain, page.ip, label="resolves_to")

    if page.title:
        urlscan_G.add_node(page.title, type="title")
        urlscan_G.add_edge(domain, page.title, label="title")

    if page.country:
        urlscan_G.add_node(page.country, type="country")
        urlscan_G.add_edge(page.ip if page.ip else domain, page.country, label="located_in")
        
    for tx in requests:
        req_url = tx.request.request.url if tx.request and tx.request.request else None
        if req_url and page.apexDomain not in req_url:
            urlscan_G.add_node(req_url, type="requested_url")
            urlscan_G.add_edge(domain, req_url, label="requests")
            
    
    # 1つのサブフロー(VTスキャンのTimeout等)が全体を道連れにしないよう
    # return_exceptions=Trueで受け、失敗フローは空グラフに縮退させる。
    virus_r, whois_r, content_r = await asyncio.gather(
        analyze_virustotal(page.url),
        analyze_whois(page.apexDomain),
        extract_page_content(result.html),
        return_exceptions=True,
    )
    virus_G = _graph_or_empty(virus_r, "VirusTotal")
    whois_G = _graph_or_empty(whois_r, "WhoIs")
    content_G = _graph_or_empty(content_r, "ページ本文抽出")

    G = nx.compose_all([urlscan_G, virus_G, whois_G, content_G])
    
    for node in content_G.nodes():
      if content_G.in_degree(node) == 0:
          G.add_edge(domain, node, label="page_content")

    # ピボット合流: WhoIsで登録者メール(type="email")が取れたら、そのメールで
    # メール系フロー(extract_mail_info)を展開し、同一emailノード上でcompose合流する
    # （＝「人物特定まで進むドメイン」）。取れなければドメイン単体で完結。
    # analyze_whoisが apex_domain --registrant_email--> email を張っているため、
    # 同一文字列のemailノードで自動的に連結する。
    registrant_emails = [n for n, d in whois_G.nodes(data=True) if d.get("type") == "email"]
    if registrant_emails:
        mail_graphs = await asyncio.gather(
            *(extract_mail_info(email) for email in registrant_emails)
        )
        G = nx.compose_all([G, *mail_graphs])

    # ハブフィルタ: AI由来ノイズを除去して見やすくする（構造化ノードは常に残す）
    G = prune_graph(G, anchor=domain)

    return G
