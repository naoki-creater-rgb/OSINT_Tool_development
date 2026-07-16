from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from typing import List

_DEFAULT_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36")

# 本文HTMLしか使わないため、重いリソースはブロックしてページ読み込みを高速化する。
_BLOCKED_RESOURCES = {"image", "media", "font", "stylesheet"}

# goto のタイムアウト(ms)。死URL/低速サイトを早く諦めてファンアウト全体を短縮。
_GOTO_TIMEOUT_MS = 15000

# domcontentloaded 後の追加待ち(ms)。以前は固定6000で全ページに課していたが、
# JS描画の落ち着きを待つ最小限に短縮する。
_SETTLE_MS = 1500


def _route_handler(route):
    """画像/動画/フォント/CSSをブロックし本文取得を高速化する。

    goto タイムアウトや browser.close() の瞬間に処理中のリクエストが残ると
    route の continue_/abort が行き場を失い CancelledError を投げるため、
    後片付け時の例外は握りつぶす（機能には影響しない）。
    """
    try:
        if route.request.resource_type in _BLOCKED_RESOURCES:
            route.abort()
        else:
            route.continue_()
    except Exception:
        pass


def get_html_with_playwright(url: str, cookies: List[dict] | None = None):
    # 1. Playwrightの起動
    with sync_playwright() as p:
        # ブラウザを起動（headless=True で画面非表示）
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=_DEFAULT_UA, locale="en-US")
        if cookies:
            context.add_cookies(cookies)

        # 設定したcontext(UA/locale/cookies)上でページを開く。
        page = context.new_page()

        # 画像/動画/フォント/CSSは本文抽出に不要なのでブロックし、転送量を削減。
        page.route("**/*", _route_handler)

        # 2. リクエストの送信
        print("Playwright: リクエストを送信中...")
        # goto がタイムアウトしても致命傷にせず、そこまでに読めた内容で続行する
        # （本文が空/薄ければ呼び出し側の本文長ゲートがLLM抽出を弾く）。
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=_GOTO_TIMEOUT_MS)
            page.wait_for_timeout(_SETTLE_MS)
        except PlaywrightTimeoutError:
            print(f"Playwright: gotoタイムアウト、取得済み内容で続行: {url}")

        # 3. レスポンスの受け取り
        # ブラウザ上にレンダリングされた最終的なHTMLを「文字列」として取得
        html_response = page.content()

        # ブロックハンドラを外してから閉じる（後片付け時の例外を減らす）。
        page.unroute("**/*", _route_handler)
        browser.close()

        return html_response

if __name__ == "__main__":
    get_html_with_playwright("https://qiita.com/Shun141/items/fbed88abd4518f6d4039")
