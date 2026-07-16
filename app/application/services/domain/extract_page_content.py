import asyncio
import time

import networkx as nx

from app.infrastructure.clients.beautifulsoup4_client import parse_with_bs4_html
from app.infrastructure.clients.kg_gen_client import relation_generate_from_text
from app.infrastructure.clients.networkx_client import generate_networkx


# WAF/ボット対策(Cloudflare等)のブロック・チャレンジページに特有の文言。
# これらの本文をAIに渡すと "security service" や "SQL command" 等の
# 対象と無関係なノードが生成されるため、AI抽出前に丸ごと弾く。
# 誤検出を避けるため、正規ページにはまず現れない特徴的な語句のみを採用する。
_BLOCK_PAGE_MARKERS = (
    "you have been blocked",
    "cloudflare ray id",
    "this website is using a security service",
    "triggered the security solution",
    "checking your browser before accessing",
    "verifying you are human",
    "enable javascript and cookies to continue",
    "performance & security by cloudflare",
    "access to this page has been denied",
)


def _looks_like_block_page(text: str) -> bool:
    """WAF/ボット対策のブロック・チャレンジページかどうかを判定する。"""
    lowered = text.lower()
    return any(marker in lowered for marker in _BLOCK_PAGE_MARKERS)


# Not Found / 存在しないプロフィールページに特有の文言。WMNの誤検知や
# 削除済みアカウントはこの種のページを返し、本文が長くても中身は無いため
# AI抽出前に弾く。単語 "not found" 単独は正規ページ本文にも現れうるので、
# 誤検出を避けて複数語のフレーズのみを採用する。
_NOT_FOUND_MARKERS = (
    "404 not found",
    "page not found",
    "page doesn't exist",
    "page does not exist",
    "page you requested",
    "page you are looking for",
    "page isn't available",
    "page is not available",
    "no longer available",
    "profile not found",
    "user not found",
    "account not found",
    "this account doesn't exist",
    "sorry, this page",
)

# AI抽出に足る最小本文長。これ未満は Not Found/空/スタブページとみなし
# LLMを走らせない（②のOllama直列コストを無駄打ちしないため）。
_MIN_CONTENT_CHARS = 200


def _looks_like_not_found(text: str) -> bool:
    """Not Found / 存在しないページかどうかをマーカーで判定する。"""
    lowered = text.lower()
    return any(marker in lowered for marker in _NOT_FOUND_MARKERS)


async def extract_page_content(html: str):
    """urlscan取得のHTMLからテキストを抽出し、AI(kg_gen)で関係グラフ化する。
    """
    clean_text = parse_with_bs4_html(html)

    # WAF/ボット対策のブロックページはAIに渡さず空グラフを返す（ノイズ源除去）。
    if _looks_like_block_page(clean_text):
        print("ブロックページ検出のためAI抽出をスキップ")
        return nx.MultiDiGraph()

    # Not Found / 存在しないプロフィールページも同様にAIへ渡さない。
    if _looks_like_not_found(clean_text):
        print("Not Foundページ検出のためAI抽出をスキップ")
        return nx.MultiDiGraph()

    # 本文が短すぎる（空/スタブ/Not Found級）ページはLLMを走らせない。
    if len(clean_text) < _MIN_CONTENT_CHARS:
        print(f"本文が短すぎるためAI抽出をスキップ（{len(clean_text)}文字）")
        return nx.MultiDiGraph()

    # kg_gen(Gemini)のレート制限対策: 長文は先頭を切り詰める。
    # 単語途中で切らないよう、上限付近の最後の改行まで戻す。
    MAX_CHARS = 2000
    if len(clean_text) > MAX_CHARS:
        clean_text = clean_text[:MAX_CHARS]
        cut = clean_text.rfind("\n")
        if cut > MAX_CHARS // 2:
            clean_text = clean_text[:cut]

    # kg.generate() は同期ブロッキング(Ollama)。async関数内で直接呼ぶと
    # イベントループ全体が停止し、gatherした他フローの並列性が消えるため、
    # 別スレッドへ退避してループを解放する（fetchとLLM生成が重なるようになる）。
    # LLM生成には進捗ログが無く「BS4の直後で無言停止」に見えるため、
    # 生成の開始/所要時間を明示してCPU-LLM律速を可視化する。
    print(f"LLM(kg_gen)生成中…（{len(clean_text)}文字）")
    _t0 = time.perf_counter()
    graph = await asyncio.to_thread(relation_generate_from_text, clean_text)
    print(f"LLM(kg_gen)生成完了（{time.perf_counter() - _t0:.1f}秒）")
    G = generate_networkx(graph)

    return G
