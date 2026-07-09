import httpx
from app.infrastructure.request_models.holehe_model import HoleheResponseModel
from typing import List
from holehe.core import import_submodules, get_functions

import asyncio

async def check_email_service(email: str) -> List[HoleheResponseModel]:
  modules = import_submodules("holehe.modules")
  websites = get_functions(modules)
  response_list = []
  
  async with httpx.AsyncClient() as client:
    tasks = [site(email, client, response_list) for site in websites]
    await asyncio.gather(*tasks, return_exceptions=True)
      
    result = [HoleheResponseModel.model_validate(response) for response in response_list]
      
    return result