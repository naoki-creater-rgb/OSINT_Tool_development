from app.infrastructure.clients.beautifulsoup4_client import parse_with_bs4_html
from app.infrastructure.clients.kg_gen_client import relation_generate_from_text
from app.infrastructure.clients.networkx_client import generate_networkx


async def extract_page_content(html: str):
    """urlscan取得のHTMLからテキストを抽出し、AI(kg_gen)で関係グラフ化する。
    """
    clean_text = parse_with_bs4_html(html)

    # kg_gen(Gemini)のレート制限対策: 長文は先頭を切り詰める。
    # 単語途中で切らないよう、上限付近の最後の改行まで戻す。
    MAX_CHARS = 2000
    if len(clean_text) > MAX_CHARS:
        clean_text = clean_text[:MAX_CHARS]
        cut = clean_text.rfind("\n")
        if cut > MAX_CHARS // 2:
            clean_text = clean_text[:cut]

    graph = relation_generate_from_text(clean_text)
    G = generate_networkx(graph)

    return G
