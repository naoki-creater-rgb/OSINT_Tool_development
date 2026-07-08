from bs4 import BeautifulSoup
import requests

def _parth_with_bs4(html: str) -> str:
  """
  BS4を使用して、テキストメッセージのみを取り出す
  """
  print("BS4: レスポンス（文字列）を解析中...")
  soup = BeautifulSoup(html, "lxml")

  print(f"変換後のデータ型: {type(soup)}")

  for script_or_style in soup(["script", "style"]):
    script_or_style.decompose()

  clean_text = soup.get_text(separator="\n", strip=True)

  print(clean_text)

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