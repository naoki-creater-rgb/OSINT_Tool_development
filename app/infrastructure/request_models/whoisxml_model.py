from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

class WhoisBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

class NameServers(WhoisBaseModel):
    """
    ネームサーバー情報
    
    Attributes:
        host_names (List[str]): ネームサーバーのホスト名リスト（例: ['ns1.google.com', ...])
    """
    host_names: List[str] = Field(default=[], alias="hostNames")

class Registrant(WhoisBaseModel):
    """
    ドメイン登録者（所有者）情報
    
    Attributes:
        organization (Optional[str]): 登録者の組織・企業名（例: 'Google LLC'）
        country (Optional[str]): 登録者の国名（例: 'UNITED STATES'）
        email (Optional[str]): 登録者のメールアドレス（プライバシー保護時は 'REDACTED FOR PRIVACY' など）
    """
    organization: Optional[str] = None
    country: Optional[str] = None
    email: Optional[str] = None

class WhoisRecord(WhoisBaseModel):
    """
    WHOISレコードのメインデータ
    
    Attributes:
        created_date (Optional[str]): ドメインの初回登録日時
        updated_date (Optional[str]): ドメイン情報の最終更新日時
        expires_date (Optional[str]): ドメインの有効期限
        registrar_name (Optional[str]): ドメインの販売・管理窓口会社（レジストラ）の名前
        registrar_iana_id (Optional[str]): レジストラに割り当てられた世界共通の識別番号
        status (Optional[str]): ドメインの現在の状態（ロック状態や凍結状態を示すスペース区切りの文字列）
        estimated_domain_age (Optional[int]): ドメインが作成されてからの推定経過日数（使い捨て検知等に利用）
        contact_email (Optional[str]): レジストラ等の不正利用（Abuse）報告用メールアドレス
        name_servers (Optional[NameServers]): 紐付けられているネームサーバー情報
        registrant (Optional[Registrant]): ドメインの所有者情報
    """
    created_date: Optional[str] = None
    updated_date: Optional[str] = None
    expires_date: Optional[str] = None
    
    registrar_name: Optional[str] = Field(default=None, alias="registrarName")
    registrar_iana_id: Optional[str] = Field(default=None, alias="registrarIANAID")
    status: Optional[str] = None
    estimated_domain_age: Optional[int] = Field(default=None, alias="estimatedDomainAge")
    
    contact_email: Optional[str] = Field(default=None, alias="contactEmail")
    
    name_servers: Optional[NameServers] = None
    registrant: Optional[Registrant] = None

    # .jp（JPRS）等では上位が空になり、実データがこの registryData 側に入る。
    # 構成が WhoisRecord のサブセットのため自己参照で再利用する。
    registry_data: Optional["WhoisRecord"] = Field(default=None, alias="registryData")

    @property
    def effective(self) -> "WhoisRecord":
        """
        実データを持つレコードを返す。

        .com 等は上位が埋まっているため self をそのまま返す。
        .jp（JPRS）等は上位が空で registry_data 側に実データが入るため、
        上位が空かつ registry_data が存在する場合はそちらを返す。
        呼び出し側は TLD を意識せず `record.effective.status` の形で参照できる。
        """
        if not self.status and not self.registrar_name and self.registry_data is not None:
            return self.registry_data
        return self

class WhoisApiResponse(BaseModel):
    """
    WHOIS APIのレスポンス最上位ルートオブジェクト
    
    Attributes:
        whois_record (WhoisRecord): WHOISの各種詳細レコードを格納するメインオブジェクト
    """
    model_config = ConfigDict(populate_by_name=True)
    whois_record: WhoisRecord = Field(alias="WhoisRecord")