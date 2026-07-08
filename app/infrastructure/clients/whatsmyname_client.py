import json
from typing import List
from naminter import Naminter
import re

from app.infrastructure.request_models.whatsmyname_model import WhatsMyNameResponse


wmn_data = json.load(open("wmn-data.json"))

async def check_user_service(username: str) -> List[WhatsMyNameResponse]:
  """
  ユーザの使用サービスを特定する
  """
  async with Naminter(wmn_data, max_tasks=50) as n:
    results = await n.check_usernames([username])
    contains_query_pattern = r"\?.*="
    contains_search_pattern = r"\/search"
    found = [WhatsMyNameResponse.model_validate(r, from_attributes=True) for r in results if r.result_status.name == "FOUND" and not (re.search(contains_query_pattern, r.result_url) or re.search(contains_search_pattern, r.result_url))]
    
    return found
