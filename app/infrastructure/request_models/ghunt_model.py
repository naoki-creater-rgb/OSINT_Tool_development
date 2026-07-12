from typing import List, Optional
from pydantic import BaseModel

class ProfilePhoto(BaseModel):
  url: Optional[str] = None #プロフィール写真のURL（逆画像検索・顔照合の起点）
  is_default: Optional[bool] = None #Trueならデフォルト画像（本人未設定）、Falseなら本人設定の写真

class ProfileData(BaseModel):
  name: Optional[str] = None #Googleアカウント名
  profile_photo: Optional[ProfilePhoto] = None #プロフィール写真

class CalendarEvent(BaseModel):
  summary: Optional[str] = None #Googleカレンダーの予定

class CalendarData(BaseModel):
  events: List[CalendarEvent] = []

class MapsReview(BaseModel):
  store_name: Optional[str] = None #レビューした店舗（場所）の名前

class MapsData(BaseModel):
  reviews: List[MapsReview] = []

class PlayGame(BaseModel):
  title: Optional[str] = None #プレイしたゲームのタイトル

class PlayGamesData(BaseModel):
  games: List[PlayGame] = []

class GoogleServices(BaseModel):
  calendar: Optional[CalendarData] = None
  maps: Optional[MapsData] = None
  play_games: Optional[PlayGamesData] = None

class GHuntResponse(BaseModel):
  gaia_id: Optional[str] = None #Googleが内部でユーザーを識別する21桁の固有ID
  profile: Optional[ProfileData] = None
  services: Optional[GoogleServices] = None
