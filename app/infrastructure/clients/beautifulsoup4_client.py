from bs4 import BeautifulSoup
import requests

def _parth_with_bs4(html: str) -> str:
  """
  BS4を使用して、本文テキストのみを取り出す。
  (a) ボイラープレート(nav/footer等)を除去し、(b) 本文コンテナに限定して
  ノイズを削減する。
  """
  print("BS4: レスポンス（文字列）を解析中...")
  soup = BeautifulSoup(html, "lxml")

  # (a) ボイラープレート除去（本文以外の定型要素を丸ごと落とす）
  for tag in soup(["script", "style", "nav", "footer", "header",
                   "aside", "form", "noscript", "svg", "iframe"]):
    tag.decompose()

  # (b) 本文コンテナに限定（main/article/role=main が無ければ body、それも無ければ全体）
  main = (soup.find("main")
          or soup.find("article")
          or soup.find(attrs={"role": "main"})
          or soup.body
          or soup)

  clean_text = main.get_text(separator="\n", strip=True)

  print(f"BS4: 抽出テキスト長 {len(clean_text)} 文字")

  return clean_text

def parse_with_bs4_url(url: str) -> str:
  """
  URLが与えられた際にBS4で解析する
  """
  response = requests.get(url)
  response.encoding = response.apparent_encoding
  html = response.text

  return _parth_with_bs4(html)

def parse_with_bs4_html(html: str) -> str:
  """
  直接HTMLテキストが与えられた際にBS4で解析する
  """

  return _parth_with_bs4(html)

if __name__ == "__main__":
  parse_with_bs4_url("https://qiita.com/Shun141/items/fbed88abd4518f6d4039")