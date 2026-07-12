from playwright.sync_api import sync_playwright
from typing import List

_DEFAULT_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36")

def get_html_with_playwright(url: str, cookies: List[dict] | None = None):
    # 1. Playwrightの起動
    with sync_playwright() as p:
        # ブラウザを起動（headless=True で画面非表示）
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=_DEFAULT_UA, locale="en-US")
        if cookies:
            context.add_cookies(cookies)
        
        page = browser.new_page()
        
        # 2. リクエストの送信
        print("Playwright: リクエストを送信中...")
        page.goto(url, wait_until="domcontentloaded")
        #ページを待機
        page.wait_for_timeout(6000)
        
        # 3. レスポンスの受け取り
        # ブラウザ上にレンダリングされた最終的なHTMLを「文字列」として取得
        html_response = page.content()
        
        # ブラウザを閉じる
        browser.close()
        
        return html_response

if __name__ == "__main__":
    get_html_with_playwright("https://qiita.com/Shun141/items/fbed88abd4518f6d4039")