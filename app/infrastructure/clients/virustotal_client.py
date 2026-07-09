import asyncio
import httpx
import os
from dotenv import load_dotenv

from app.infrastructure.request_models.virustotal_client import (
    VirusTotalResponse,
    VirusTotalFirstResponse,
    VirusTotalAnalysisResponse,
)

load_dotenv(".env")

VIRUSTOTAL_URL = os.getenv("VIRUSTOTAL_URL")
VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")

POLL_MAX_ATTEMPTS = 48
POLL_INTERVAL_SEC = 5 

async def virustotal_response(domain: str) -> VirusTotalResponse:
  async with httpx.AsyncClient() as client:
    request_url = f"{VIRUSTOTAL_URL}/urls"
    
    header = {"x-apikey": VIRUSTOTAL_API_KEY, "accept": "application/json"}
    request_params = {"url": domain}
    
    request_response = await client.post(request_url, headers = header, data = request_params)
    request_response.raise_for_status()

    analysis_id = VirusTotalFirstResponse.model_validate_json(request_response.text).data.id

    result_url = f"{VIRUSTOTAL_URL}/analyses/{analysis_id}"

    for _ in range(POLL_MAX_ATTEMPTS):
      analysis_response = await client.get(result_url, headers = header)
      analysis_response.raise_for_status()
      analysis = VirusTotalAnalysisResponse.model_validate_json(analysis_response.text)

      if analysis.data.attributes.status == "completed":
        # /analyses は完了判定のみ。malicious 判定と解説は URLオブジェクト側にある
        url_id = analysis.meta.url_info.id if analysis.meta and analysis.meta.url_info else None
        if not url_id:
          raise ValueError("分析は完了したが meta.url_info.id が取得できませんでした")

        url_response = await client.get(f"{VIRUSTOTAL_URL}/urls/{url_id}", headers = header)
        url_response.raise_for_status()
        return VirusTotalResponse.model_validate_json(url_response.text)

      await asyncio.sleep(POLL_INTERVAL_SEC)

    raise TimeoutError(
      f"スキャンが {POLL_INTERVAL_SEC * POLL_MAX_ATTEMPTS} 秒以内に完了しませんでした"
    )

