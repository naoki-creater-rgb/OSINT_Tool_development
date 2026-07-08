from app.infrastructure.request_models import WhoisApiResponse
import asyncio
import os

import httpx
from dotenv import load_dotenv

load_dotenv(".env")

WHOISXML_URL = os.getenv("WHOISXML_URL")
WHOISXML_API_KEY = os.getenv("WHOISXML_API_KEY")

async def get_whoisxml(domain_name: str) -> WhoisApiResponse:
  async with httpx.AsyncClient() as client:
    params = {"apiKey": WHOISXML_API_KEY, "domainName": domain_name, "outputFormat": "JSON"}
    response = await client.get(WHOISXML_URL, params=params)
    
    return WhoisApiResponse.model_validate(response.json())