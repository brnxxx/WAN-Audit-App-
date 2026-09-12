from datetime import datetime
from typing import Optional
from pydantic import BaseModel, model_validator


class LoginRequest(BaseModel):
    username: str
    password: str


class AdminOut(BaseModel):
    id: int
    username: str
    email: str | None = None
    is_active: bool
    last_login: datetime | None = None

    class Config:
        from_attributes = True


# ---------- Sites ----------

class SiteCreate(BaseModel):
    name: str
    description: str | None = None
    location: str | None = None


class SiteOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    location: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Backbone ----------

class BackboneCreate(BaseModel):
    name: str
    description: str | None = None


class BackboneOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Devices ----------

class DeviceCreate(BaseModel):
    name: str
    hostname: str | None = None
    ip_address: str | None = None
    device_type: str  # router | firewall | switch | server | cloud | other
    vendor: str | None = None
    model: str | None = None
    site_id: Optional[int] = None
    backbone_id: Optional[int] = None
    management_protocol: str = "ssh"
    username: str | None = None
    port: int | None = None

    @model_validator(mode="after")
    def check_site_xor_backbone(self):
        if (self.site_id is None) == (self.backbone_id is None):
            raise ValueError(
                "Un device doit avoir soit site_id soit backbone_id, jamais les deux ni aucun."
            )
        return self


class DeviceOut(BaseModel):
    id: int
    name: str
    hostname: str | None = None
    ip_address: str | None = None
    device_type: str
    vendor: str | None = None
    model: str | None = None
    site_id: int | None = None
    backbone_id: int | None = None
    status: str
    management_protocol: str
    username: str | None = None
    port: int | None = None
    site_name: str | None = None
    backbone_name: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------- Interfaces ----------

class InterfaceCreate(BaseModel):
    device_id: int
    name: str
    ip_address: str | None = None
    subnet_mask: str | None = None
    mac_address: str | None = None
    status: str = "unknown"
    speed: str | None = None
    description: str | None = None


class InterfaceOut(BaseModel):
    id: int
    device_id: int
    name: str
    ip_address: str | None = None
    subnet_mask: str | None = None
    mac_address: str | None = None
    status: str
    speed: str | None = None
    description: str | None = None

    class Config:
        from_attributes = True