import asyncio
import os

from dotenv import load_dotenv

from ghunt.objects.base import GHuntCreds
from ghunt.helpers.utils import get_httpx_client
from ghunt.helpers import auth, gmaps, playgames, calendar as gcalendar
from ghunt.apis.peoplepa import PeoplePaHttp

from app.infrastructure.request_models.ghunt_model import (
    GHuntResponse,
    ProfileData,
    ProfilePhoto,
    GoogleServices,
    CalendarData,
    CalendarEvent,
    MapsData,
    MapsReview,
    PlayGamesData,
    PlayGame,
)

load_dotenv(".env")

# 調査用Googleアカウントの master token（aas_et/… で始まる長期クレデンシャル）
GHUNT_MASTER_TOKEN = os.getenv("GHUNT_MASTER_TOKEN")

# people_lookup が返すコンテナ名。公開Googleアカウントは "PROFILE" に入る
CONTAINER = "PROFILE"


async def ensure_creds(as_client) -> GHuntCreds:
    """認証済み GHuntCreds を用意する（対話的な `ghunt login` は不要）。

    - 有効な creds.m が既にあればそれをロード＋検証して返す。
    - 無ければ環境変数の master token から cookies/osids を再生成して保存する。

    master token は失効させない限り長期間有効なため、
    通常は一度保存すれば以降は creds.m の自動再検証だけで動作する。
    """
    creds = GHuntCreds()

    # 1. 既存の creds.m が使えるならそれを使う
    try:
        creds.load_creds(silent=True)
        if creds.are_creds_loaded():
            # cookies の検証と必要に応じた再生成を行う
            await auth.check_and_gen(as_client, creds)
            return creds
    except Exception:
        pass  # creds.m が無い / 壊れている → master token から再構築へ

    # 2. master token から非対話でセッションを構築（login.py の master token パス相当）
    if not GHUNT_MASTER_TOKEN:
        raise RuntimeError(
            "GHUNT_MASTER_TOKEN が未設定です。調査用Googleアカウントで一度 "
            "`ghunt login` を実行し、生成された master token を .env に設定してください。"
        )

    creds.android.master_token = GHUNT_MASTER_TOKEN
    creds.android.authorization_tokens = {}
    creds.cookies = {"a": "a"}  # ダミー（gen_cookies_and_osids で本物に置換される）
    creds.osids = {"a": "a"}
    await auth.gen_cookies_and_osids(as_client, creds)
    creds.save_creds(silent=True)
    return creds


async def ghunt_response(target_email: str) -> GHuntResponse | None:
    """メールアドレスから GHunt で公開Googleアカウント情報を収集して返す。

    認証は master token（環境変数 GHUNT_MASTER_TOKEN）から自動で行うため、
    対話的な `ghunt login` の事前実行は不要。
    """
    as_client = get_httpx_client()

    try:
        # 1. 認証情報の用意＋認証（creds.m が無ければ master token から自動生成）
        creds = await ensure_creds(as_client)

        # 2. プロフィール本体を取得（これが調査の中核）
        people_pa = PeoplePaHttp(creds)
        is_found, target = await people_pa.people_lookup(
            as_client, target_email, params_template="max_details"
        )
        if not is_found or CONTAINER not in target.sourceIds:
            # 公開Googleアカウントに紐づかなかった場合
            return None

        # 3. プロフィール名
        name = (
            target.names[CONTAINER].fullname
            if CONTAINER in target.names else None
        )

        # 3-2. プロフィール写真（本人設定なら逆画像検索・顔照合の起点になる）
        profile_photo = None
        if CONTAINER in target.profilePhotos:
            photo = target.profilePhotos[CONTAINER]
            profile_photo = ProfilePhoto(url=photo.url, is_default=photo.isDefault)

        # 4. Maps レビュー（店名）
        #    ⚠️ GHunt 2.3.4 の gmaps.get_reviews は「統計（件数）」しか返さない。
        #    店名を含むレビュー本体の取得ループは upstream でコメントアウトされているため、
        #    現状 reviews は常に空になる。将来ライブラリ側が対応したら populate される。
        _, maps_stats = await gmaps.get_reviews(as_client, target.personId)
        maps = MapsData(reviews=[])  # store_name は現バージョンでは取得不可

        # 5. Play Games（ゲームタイトル）
        games: list[PlayGame] = []
        players = await playgames.search_player(creds, as_client, target_email)
        if players:
            is_player_found, player = await playgames.get_player(
                creds, as_client, players[0].id
            )
            if is_player_found and player.played_games:
                games = [
                    PlayGame(title=g.game_data.name)
                    for g in player.played_games
                    if g.game_data and g.game_data.name
                ]
        play_games = PlayGamesData(games=games)

        # 6. Calendar（公開カレンダーの予定名）
        events: list[CalendarEvent] = []
        cal_found, _, calendar_events = await gcalendar.fetch_all(
            creds, as_client, target_email
        )
        if cal_found and calendar_events and calendar_events.items:
            events = [
                CalendarEvent(summary=ev.summary) for ev in calendar_events.items
            ]
        calendar = CalendarData(events=events)

        return GHuntResponse(
            gaia_id=target.personId,
            profile=ProfileData(name=name, profile_photo=profile_photo),
            services=GoogleServices(
                calendar=calendar,
                maps=maps,
                play_games=play_games,
            ),
        )
    finally:
        await as_client.aclose()
        
def to_playwright_cookies(cookie_dict: dict) -> list[dict]:
    """Googleのcookies(name->value)をPlaywrightのadd_cookies形式へ変換。
    __Host- はDomain属性禁止のため url指定(host-only)にする。"""
    out = []
    for name, value in cookie_dict.items():
        if name.startswith("__Host-"):
            out.append({"name": name, "value": value,
                        "url": "https://www.google.com",
                        "secure": True, "sameSite": "None"})
        else:
            out.append({"name": name, "value": value,
                        "domain": ".google.com", "path": "/",
                        "secure": True, "sameSite": "None"})
    return out


async def get_ghunt_cookies() -> list[dict]:
    """GHunt認証セッションのCookieをPlaywright形式で返す（共通利用）。"""
    as_client = get_httpx_client()
    try:
        creds = await ensure_creds(as_client)
        return to_playwright_cookies(creds.cookies)
    finally:
        await as_client.aclose()


if __name__ == "__main__":
    result = asyncio.run(ghunt_response("investigate_target@gmail.com"))
    print(result.model_dump_json(indent=2) if result else "Not found.")
