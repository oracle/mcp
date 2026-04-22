from datetime import datetime

from pydantic import BaseModel, Field


class ToolErrorPayload(BaseModel):
    code: str
    message: str
    resource_type: str | None = None
    retry_hint: str | None = None
    details: dict = Field(default_factory=dict)


class DomainContextModel(BaseModel):
    iot_domain_id: str
    iot_domain_display_name: str | None = None
    iot_domain_group_id: str
    iot_domain_group_display_name: str | None = None
    device_host: str
    data_host: str
    domain_short_id: str
    domain_group_short_id: str
    region: str
    db_token_scope: str | None = None
    db_allowed_identity_domain_host: str | None = None


class DataApiTokenModel(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    expires_at: datetime


def success_result(data: dict) -> dict:
    return {"ok": True, "data": data}
