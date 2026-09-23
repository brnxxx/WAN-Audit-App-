from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator, model_validator


VALID_DEVICE_TYPES = {"router", "firewall", "switch", "server", "cloud", "other"}
VALID_MANAGEMENT_PROTOCOLS = {"ssh", "telnet", "http", "https", "none"}
VALID_INTERFACE_STATUS = {"up", "down", "unknown"}


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

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Le nom du site ne peut pas être vide")
        return cleaned


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

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Le nom du backbone ne peut pas être vide")
        return cleaned


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

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Le nom du device ne peut pas être vide")
        return cleaned

    @field_validator("device_type")
    @classmethod
    def validate_device_type(cls, value: str) -> str:
        if value not in VALID_DEVICE_TYPES:
            raise ValueError(f"device_type invalide. Valeurs autorisées : {sorted(VALID_DEVICE_TYPES)}")
        return value

    @field_validator("management_protocol")
    @classmethod
    def validate_management_protocol(cls, value: str) -> str:
        if value not in VALID_MANAGEMENT_PROTOCOLS:
            raise ValueError(
                f"management_protocol invalide. Valeurs autorisées : {sorted(VALID_MANAGEMENT_PROTOCOLS)}"
            )
        return value

    @field_validator("ip_address")
    @classmethod
    def validate_ip_address(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            return None
        return cleaned

    @model_validator(mode="after")
    def check_site_xor_backbone(self):
        if (self.site_id is None) == (self.backbone_id is None):
            raise ValueError(
                "Un device doit avoir soit site_id soit backbone_id, jamais les deux ni aucun."
            )
        return self


class DeviceUpdate(BaseModel):
    """Full update payload; clearing an assignment is a supported operation."""

    name: str
    hostname: str | None = None
    ip_address: str | None = None
    device_type: str
    vendor: str | None = None
    model: str | None = None
    site_id: int | None = None
    backbone_id: int | None = None
    management_protocol: str = "ssh"
    username: str | None = None
    port: int | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Le nom du device ne peut pas être vide")
        return cleaned

    @field_validator("device_type")
    @classmethod
    def validate_device_type(cls, value: str) -> str:
        if value not in VALID_DEVICE_TYPES:
            raise ValueError(f"device_type invalide. Valeurs autorisées : {sorted(VALID_DEVICE_TYPES)}")
        return value

    @field_validator("management_protocol")
    @classmethod
    def validate_management_protocol(cls, value: str) -> str:
        if value not in VALID_MANAGEMENT_PROTOCOLS:
            raise ValueError(
                f"management_protocol invalide. Valeurs autorisées : {sorted(VALID_MANAGEMENT_PROTOCOLS)}"
            )
        return value

    @model_validator(mode="after")
    def check_location(self):
        if self.site_id is not None and self.backbone_id is not None:
            raise ValueError("Un device ne peut pas appartenir à un site et un backbone simultanément.")
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

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Le nom de l'interface ne peut pas être vide")
        return cleaned

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in VALID_INTERFACE_STATUS:
            raise ValueError(f"status invalide. Valeurs autorisées : {sorted(VALID_INTERFACE_STATUS)}")
        return value

    @field_validator("ip_address")
    @classmethod
    def validate_ip_address(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            return None
        return cleaned


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