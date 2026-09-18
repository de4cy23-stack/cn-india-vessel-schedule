from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


CarrierStatus = Literal["ready", "reserved", "disabled"]


class ScheduleLeg(BaseModel):
    pol: str | None = None
    pod: str | None = None
    vessel: str | None = None
    voyage: str | None = None
    etd: datetime | None = None
    eta: datetime | None = None


class Schedule(BaseModel):
    carrier: str
    carrier_code: str
    origin: str
    destination: str
    vessel: str | None = None
    voyage: str | None = None
    service: str | None = None
    etd: datetime | None = None
    eta: datetime | None = None
    transit_days: float | None = None
    direct: bool | None = None
    transshipment_ports: list[str] = Field(default_factory=list)
    legs: list[ScheduleLeg] = Field(default_factory=list)
    source: str = "official_api"
    source_updated_at: datetime | None = None


class ScheduleQuery(BaseModel):
    origin: str
    destination: str
    date_from: date
    date_to: date


class CarrierInfo(BaseModel):
    slug: str
    name: str
    code: str
    status: CarrierStatus
    integration: str
