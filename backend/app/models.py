from datetime import datetime
from sqlalchemy import (
    String, Boolean, DateTime, Text, Integer, BigInteger, Float,
    ForeignKey, Enum, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(150), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    devices: Mapped[list["Device"]] = relationship(back_populates="site", cascade="all, delete-orphan")


class Backbone(Base):
    __tablename__ = "backbone"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    devices: Mapped[list["Device"]] = relationship(back_populates="backbone", cascade="all, delete-orphan")


class Device(Base):
    __tablename__ = "devices"
    console_host: Mapped[str | None] = mapped_column(String(45), nullable=True)
    console_port: Mapped[int | None] = mapped_column(Integer, nullable=True)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    hostname: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    device_type: Mapped[str] = mapped_column(
        Enum("router", "firewall", "switch", "server", "cloud", "other", name="device_type_enum"),
        nullable=False,
    )
    vendor: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)

    site_id: Mapped[int | None] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"), nullable=True)
    backbone_id: Mapped[int | None] = mapped_column(ForeignKey("backbone.id", ondelete="CASCADE"), nullable=True)

    status: Mapped[str] = mapped_column(
        Enum("online", "offline", "warning", "unknown", name="device_status_enum"),
        default="unknown",
    )
    gns3_node_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    gns3_project_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    management_protocol: Mapped[str] = mapped_column(
        Enum("ssh", "telnet", "http", "https", "none", name="mgmt_protocol_enum"),
        default="ssh",
    )
    username: Mapped[str | None] = mapped_column(String(50), nullable=True)
    port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    site: Mapped["Site | None"] = relationship(back_populates="devices")
    backbone: Mapped["Backbone | None"] = relationship(back_populates="devices")
    interfaces: Mapped[list["Interface"]] = relationship(back_populates="device", cascade="all, delete-orphan")
    metrics: Mapped[list["DeviceMetric"]] = relationship(back_populates="device", cascade="all, delete-orphan")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="device", cascade="all, delete-orphan")
    @property
    def site_name(self) -> str | None:
        return self.site.name if self.site else None

    @property
    def backbone_name(self) -> str | None:
        return self.backbone.name if self.backbone else None


class Interface(Base):
    __tablename__ = "interfaces"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    subnet_mask: Mapped[str | None] = mapped_column(String(45), nullable=True)
    mac_address: Mapped[str | None] = mapped_column(String(17), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("up", "down", "unknown", name="interface_status_enum"), default="unknown"
    )
    speed: Mapped[str | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    traffic_in: Mapped[int] = mapped_column(BigInteger, default=0)
    traffic_out: Mapped[int] = mapped_column(BigInteger, default=0)
    errors_in: Mapped[int] = mapped_column(Integer, default=0)
    errors_out: Mapped[int] = mapped_column(Integer, default=0)

    device: Mapped["Device"] = relationship(back_populates="interfaces")
    metrics: Mapped[list["InterfaceMetric"]] = relationship(back_populates="interface", cascade="all, delete-orphan")


class DeviceMetric(Base):
    __tablename__ = "device_metrics"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    cpu_usage: Mapped[float | None] = mapped_column(Float, nullable=True)
    memory_usage: Mapped[float | None] = mapped_column(Float, nullable=True)
    latency: Mapped[float | None] = mapped_column(Float, nullable=True)
    packet_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    uptime: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    device: Mapped["Device"] = relationship(back_populates="metrics")


class InterfaceMetric(Base):
    __tablename__ = "interface_metrics"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    interface_id: Mapped[int] = mapped_column(ForeignKey("interfaces.id", ondelete="CASCADE"), nullable=False)
    traffic_in: Mapped[int] = mapped_column(BigInteger, default=0)
    traffic_out: Mapped[int] = mapped_column(BigInteger, default=0)
    packets_in: Mapped[int] = mapped_column(BigInteger, default=0)
    packets_out: Mapped[int] = mapped_column(BigInteger, default=0)
    errors_in: Mapped[int] = mapped_column(Integer, default=0)
    errors_out: Mapped[int] = mapped_column(Integer, default=0)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    interface: Mapped["Interface"] = relationship(back_populates="metrics")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(
        Enum("low", "medium", "high", "critical", name="alert_severity_enum"), default="medium"
    )
    status: Mapped[str] = mapped_column(
        Enum("open", "acknowledged", "resolved", name="alert_status_enum"), default="open"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    device: Mapped["Device"] = relationship(back_populates="alerts")


class GNS3Project(Base):
    __tablename__ = "gns3_projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class InfrastructureLog(Base):
    __tablename__ = "infrastructure_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    source: Mapped[str | None] = mapped_column(String(150), nullable=True)
    target: Mapped[str | None] = mapped_column(String(45), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)


class TopologyLink(Base):
    __tablename__ = "topology_links"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    gns3_link_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    destination_device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    source_interface: Mapped[str | None] = mapped_column(String(50), nullable=True)
    destination_interface: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("up", "down", "unknown", name="link_status_enum"), default="unknown"
    )