from pydantic import BaseModel
from app.infrastructure.request_models.url_scan_io_model import UrlScanResponseRoot

class UrlScanIoResponseModel(BaseModel):
  analysis: UrlScanResponseRoot
  html: str