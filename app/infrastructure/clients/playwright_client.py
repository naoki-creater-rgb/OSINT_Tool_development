from playwright.sync_api import sync_playwright

def get_html_with_playwright(url: str):
    # 1. Playwrightの起動
    with sync_playwright() as p:
        # ブラウザを起動（headless=True で画面非表示）
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 2. リクエストの送信
        print("Playwright: リクエストを送信中...")
        page.goto(url)
        
        # 3. レスポンスの受け取り
        # ブラウザ上にレンダリングされた最終的なHTMLを「文字列」として取得
        html_response = page.content()
        
        # ブラウザを閉じる
        browser.close()
        
        # 受け取ったレスポンス（形式：str）を確認
        print(f"受け取ったデータ型: {type(html_response)}")
        print("--- レスポンス（冒頭500文字） ---")
        print(html_response[:500])
        
        return html_response

if __name__ == "__main__":
    get_html_with_playwright("https://qiita.com/Shun141/items/fbed88abd4518f6d4039")