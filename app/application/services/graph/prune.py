import networkx as nx

# アンカー(こちらが注入した接続)ラベル。ノードの「本当の関係数」には数えない。
ANCHOR_LABELS = {"page_content", "analysis_detail"}

# 構造化情報と重複する汎用語。AI由来でこれらは価値が低いため除去する。
GENERIC_WORDS = {"domain", "url", "website", "page", "date created", "ip", "email"}


def _real_relation_count(G, n):
    """page_content/analysis_detail 以外のエッジ(=実際の関係)の本数(入出合計)。"""
    cnt = 0
    for _, _, d in G.in_edges(n, data=True):
        if d.get("label") not in ANCHOR_LABELS:
            cnt += 1
    for _, _, d in G.out_edges(n, data=True):
        if d.get("label") not in ANCHOR_LABELS:
            cnt += 1
    return cnt


def _drop_isolated_wmn(H):
    """WhatsMyName由来の「孤立ヒット」を枝ごと除去する。

    WMNの構造:
        account_name --may use--> service --profile url--> url --page content--> AI

    アカウント名(例: 姓)は一意でないため、大半のヒットは同名別人。裏付けの
    無いヒットは "account_name 経由でしか本体グラフに繋がらない孤立枝" になる。

    判定: account_name ノードを外した無向グラフの連結成分のうち、
      - WMNのservice を含み、かつ
      - 成分が WMNヒットのノード(service/url/その配下のpage content子孫)だけで
        構成され、信頼コア(email/Holehe/GHunt/ドメイン等)に一切触れない
    ものを「孤立」とみなし、成分ごと削除する。逆に本文がコアへ直結している
    ヒットは成分がコアを含むため残る(=本物は守られる)。

    WMN固有のエッジラベルだけで判定するためflow非依存。
    """
    services = set()
    account_names = set()
    for u, v, d in H.edges(data=True):
        if d.get("label") == "may use":
            account_names.add(u)
            services.add(v)
    if not services:
        return H  # WMNを含まないグラフ(ドメイン単体等)は素通り

    service_url = {
        u: v for u, v, d in H.edges(data=True)
        if d.get("label") == "profile url" and u in services
    }
    urls = set(service_url.values())

    # 各urlのpage content子孫を集めてWMNヒットのノード集合を作る。
    wmn_nodes = set(services) | urls
    for url in urls:
        stack = [url]
        while stack:
            x = stack.pop()
            for _, c, d in H.out_edges(x, data=True):
                if d.get("label") == "page content" and c not in wmn_nodes:
                    wmn_nodes.add(c)
                    stack.append(c)

    # account_name を外した無向グラフの連結成分で「コア非接触」を判定。
    U = H.to_undirected()
    U.remove_nodes_from(account_names)

    drop = set()
    for comp in nx.connected_components(U):
        if not (comp & services):
            continue  # WMNヒットを含まない成分は対象外
        if comp <= wmn_nodes:
            # 成分がWMNノードだけ = コアに触れない孤立枝 → 丸ごと削除
            drop |= comp

    H = H.copy()
    H.remove_nodes_from(drop)
    return H


def prune_graph(G, anchor, min_relations: int = 2, drop_isolated_wmn: bool = True):
    """ハブフィルタ: AI由来ノイズを除去してグラフを見やすくする。

    - 構造化ノード(type属性あり)は常に残す。
    - AI由来ノード(type無し)は「本当の関係数 >= min_relations」かつ
      「汎用語でない」時だけ残す。
    - 除去で島が生じたら anchor(ドメイン)へ再接続して連結を保つ。

    ローカルLLMの抽出が貧弱でも壊れず、モデル強化で関係が増えれば
    自動的に残るハブが増える(設計はモデル品質に非依存)。
    """
    drop = []
    for n, d in G.nodes(data=True):
        if d.get("type") is not None:
            continue  # 構造化ノードは保持
        if str(n).strip().lower() in GENERIC_WORDS:
            drop.append(n)
            continue
        if _real_relation_count(G, n) < min_relations:
            drop.append(n)

    H = G.copy()
    H.remove_nodes_from(drop)

    # WMN由来の孤立ヒット(同名別人ノイズ)を枝ごと除去する。
    if drop_isolated_wmn:
        H = _drop_isolated_wmn(H)

    # 島防止: anchor と繋がっていない残存コンポーネントを anchor へ再接続する。
    if anchor in H:
        UH = H.to_undirected()
        for comp in nx.connected_components(UH):
            if anchor not in comp:
                rep = max(comp, key=lambda x: H.degree(x))  # 代表1ノードを繋ぐ
                H.add_edge(anchor, rep, label="page_content")

    return H
