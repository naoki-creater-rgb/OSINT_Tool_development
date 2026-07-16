import html as html_lib

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

  # 二重エンコード等で残るHTMLエンティティ(&#x27; 等)を実文字へ戻す。
  clean_text = html_lib.unescape(clean_text)

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

def select_texts_from_html(html: str, selector: str) -> list[str]:
  """
  HTMLから指定CSSセレクタに一致する要素のテキストを抽出する（汎用）。
  本文テキスト抽出(_parth_with_bs4)と異なり、構造化された要素を直接取り出す用途。
  """
  soup = BeautifulSoup(html, "lxml")

  return [text for el in soup.select(selector)
          if (text := el.get_text(strip=True))]

def select_records_from_html(html: str, item_selector: str,
                             field_selectors: dict[str, str]) -> list[dict]:
  """
  HTMLからitem_selectorで区切られた各コンテナごとに、field_selectorsで
  指定した複数フィールドをまとめて抽出する（汎用）。
  select_texts_from_htmlが単一フィールドのフラットなリストを返すのに対し、
  こちらはコンテナ単位で複数フィールドをひも付けたレコード列を返す。
  該当要素が無いフィールドはNoneになる。
  """
  soup = BeautifulSoup(html, "lxml")

  records = []
  for item in soup.select(item_selector):
    record = {}
    for field, selector in field_selectors.items():
      el = item.select_one(selector)
      record[field] = el.get_text(strip=True) if el else None
    records.append(record)
  return records

if __name__ == "__main__":
  parse_with_bs4_url("https://qiita.com/Shun141/items/fbed88abd4518f6d4039")