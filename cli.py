"""OSINT調査ツール MVP CLI。

  python3 cli.py https://example.com          # URL → domainモードと自動判定
  python3 cli.py someone@example.com          # メール → emailモードと自動判定
  python3 cli.py --mode email foo@bar.com     # モード明示
  python3 cli.py foo@bar.com --follow-wmn     # WMNヒット先の本文まで追跡（低速）
  python3 cli.py                              # 引数なし → 対話でモード選択

進捗は各フロー内クライアントのログがそのままコンソールに流れる。
結果は関係グラフをスタンドアロンHTMLとして書き出す。
"""
import argparse
import asyncio

from app.application.services.domain.extract_domain_info import extract_domain_info
from app.application.services.domain.extract_mail_info import extract_mail_info
from app.presentation.render_html import render_graph


def _default_out(target: str) -> str:
  safe = (target.replace("https://", "").replace("http://", "")
          .replace("@", "_at_").replace("/", "_").replace(":", "").replace(".", "_"))
  return f"result_{safe}.html"


async def run(
  mode: str, target: str, out: str,
  follow_wmn: bool = False, follow_gravatar: bool = False,
) -> None:
  print(f"[*] mode={mode}  target={target}")
  print("[*] 調査開始…（各フローの進捗はこの下に出ます）")

  if mode == "email":
    G = await extract_mail_info(
      target, follow_wmn_urls=follow_wmn, follow_gravatar_urls=follow_gravatar
    )
  else:
    G = await extract_domain_info(target)

  print(f"[+] 完了: ノード{G.number_of_nodes()} / エッジ{G.number_of_edges()}")
  if mode == "domain":
    emails = [n for n, d in G.nodes(data=True) if d.get("type") == "email"]
    print(f"[+] ピボット: {'発火 ' + ', '.join(emails) if emails else '無し（ドメイン単体で完結）'}")

  render_graph(G, out, heading=f"{mode}: {target}")
  print(f"[+] 結果HTML: {out}")


def main() -> None:
  p = argparse.ArgumentParser(description="ドメイン/メールアドレスのOSINT調査（MVP）")
  p.add_argument("target", nargs="?", help="調査対象（URL または メールアドレス）")
  p.add_argument("--mode", choices=["domain", "email", "auto"], default="auto",
                 help="調査モード。auto は @ の有無で自動判定（既定）")
  p.add_argument("--out", help="出力HTMLパス（既定: result_<target>.html）")
  p.add_argument("--follow-wmn", action="store_true",
                 help="WhatsMyNameヒット先のプロフィール本文まで追跡しAI抽出する（低速・emailモードのみ）")
  p.add_argument("--follow-gravatar", action="store_true",
                 help="Gravatar連携サービスのアカウントURL先まで追跡しAI抽出する（低速・emailモードのみ）")
  a = p.parse_args()

  target = a.target or input("調査対象（URL / メールアドレス）> ").strip()
  if not target:
    p.error("調査対象が指定されていません")

  mode = a.mode
  if mode == "auto":
    mode = "email" if "@" in target else "domain"

  out = a.out or _default_out(target)
  if mode != "email" and (a.follow_wmn or a.follow_gravatar):
    print("[!] --follow-wmn / --follow-gravatar は email モードのみ有効です。無視します。")
  asyncio.run(run(mode, target, out,
                  follow_wmn=a.follow_wmn, follow_gravatar=a.follow_gravatar))


if __name__ == "__main__":
  main()
