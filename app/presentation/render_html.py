"""関係グラフ(networkx MultiDiGraph)を pyvis のスタンドアロンHTMLへ描画する。

CLI/テストランナー共通の描画層。ノードは type ごとに色分けし、属性は
ホバー用ツールチップに載せる。ここは描画のみを担い、グラフ構築は
サービス層(extract_*_info)の責務。
"""
import html as html_lib

import networkx as nx
from pyvis.network import Network

TYPE_COLORS = {
  "email": "#e63946",
  "github_account": "#6f42c1",
  "repository": "#8957e5",
  "gaia_id": "#1a73e8",
  "account_name": "#f4a261",
  "profile_photo": "#00a3a3",
  "calendar_event": "#2a9d8f",
  "maps_review": "#2a9d8f",
  "play_game": "#2a9d8f",
  "use_service": "#2a9d8f",
  "service name": "#457b9d",
  "recoverymail": "#e76f51",
  "url": "#0077b6",
  # ドメイン系
  "domain": "#e63946",
  "apex_domain": "#d62828",
  "ip": "#0077b6",
  "title": "#adb5bd",
  "country": "#2a9d8f",
  "registrar": "#6f42c1",
  "name_server": "#457b9d",
  "organization": "#f4a261",
  "requested_url": "#90caf9",
}
DEFAULT_COLOR = "#adb5bd"


def render_graph(G: nx.MultiDiGraph, out_path: str, heading: str) -> None:
  """グラフGを out_path にスタンドアロンHTMLとして書き出す。"""
  net = Network(height="800px", width="100%", directed=True,
                bgcolor="#ffffff", heading=heading)
  net.barnes_hut()
  for n, d in G.nodes(data=True):
    color = TYPE_COLORS.get(d.get("type"), DEFAULT_COLOR)
    label = d.get("label") or str(n)
    tip = "<br>".join(f"{k}: {html_lib.escape(str(v))}" for k, v in d.items()) or "(AI由来ノード)"
    net.add_node(str(n), label=label, title=tip, color=color)
  for s, o, d in G.edges(data=True):
    net.add_edge(str(s), str(o), title=d.get("label", ""), label=d.get("label", ""))
  net.set_options('{"edges":{"font":{"size":9},"color":{"color":"#cccccc"}},"physics":{"stabilization":{"iterations":200}}}')
  net.write_html(out_path, notebook=False)
