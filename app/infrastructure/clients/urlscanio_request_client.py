import asyncio
import os

import httpx
from dotenv import load_dotenv

from app.infrastructure.request_models.url_scan_io_model import UrlScanIoUrlModel, UrlScanResponseRoot
from app.infrastructure.final_response_model.url_scan_io_response_model import UrlScanIoResponseModel

load_dotenv(".env")

SCAN_URL = os.getenv("URL_SCAN_URL")
API_KEY = os.getenv("URL_SCAN_API_KEY")

# ポーリング設定
POLL_INTERVAL_SEC = 5      # 何秒おきに結果を確認するか
POLL_MAX_ATTEMPTS = 24     # 最大試行回数（5秒 × 24 = 最大120秒待つ）


async def _submit_scan(client: httpx.AsyncClient, target_url: str) -> UrlScanIoUrlModel:
    """urlscan.io にスキャンを依頼し、受付結果（uuid・結果URL）を返す。"""
    header = {"Content-Type": "application/json", "API-Key": API_KEY}
    payload = {"url": target_url, "visibility": "public"}

    response = await client.post(SCAN_URL, headers=header, json=payload)
    response.raise_for_status()
    return UrlScanIoUrlModel.model_validate(response.json())


async def _fetch_result(client: httpx.AsyncClient, api_url: str) -> UrlScanResponseRoot:
    """
    スキャン結果を取得する。
    未完了の間(HTTP 404)は POLL_INTERVAL_SEC 秒おきに再試行し、
    完了(HTTP 200)したら解析結果をモデルにして返す。
    """
    header = {"API-Key": API_KEY}

    for _ in range(POLL_MAX_ATTEMPTS):
        response = await client.get(api_url, headers=header)

        if response.status_code == 200:
            # スキャン完了 → 解析結果をモデルに適応して返す
            return UrlScanResponseRoot.model_validate(response.json())

        if response.status_code == 404:
            # まだスキャン中 → 待機してから再試行
            await asyncio.sleep(POLL_INTERVAL_SEC)
            continue

        # 想定外のステータス（認証エラー等）はそのまま例外に
        response.raise_for_status()

    raise TimeoutError(
        f"スキャンが {POLL_INTERVAL_SEC * POLL_MAX_ATTEMPTS} 秒以内に完了しませんでした"
    )
    
async def _get_web_page(client: httpx.AsyncClient, uuid: str) -> str:
    """
    解析の結果取得できたHTMLを取得する
    """
    request_url = f"https://urlscan.io/dom/{uuid}/"
    header = {"API-KEY": API_KEY}
    
    response = await client.get(request_url, headers = header)
    
    if response.status_code == 200:
        return response.text
    else:
        return "データの取得失敗"


async def scan_url(target_url: str) -> UrlScanIoResponseModel:
    """スキャン依頼 → 完了待ち → 解析結果取得 & HTMLデータ取得を一括で行う。"""
    async with httpx.AsyncClient(timeout=30) as client:
        submit = await _submit_scan(client, target_url)
        analysis_data = await _fetch_result(client, submit.api)
        html_data = await _get_web_page(client, submit.uuid)
        
        url_result = UrlScanIoResponseModel(analysis = analysis_data, html = html_data)
        
        return url_result