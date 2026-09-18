from __future__ import annotations

import os

from app.adapters.configured import (
    CmaCgmAdapter,
    HapagLloydAdapter,
    HmmAdapter,
    MaerskAdapter,
    OneAdapter,
)
from app.models import CarrierInfo


READY = [
    ("MAERSK", MaerskAdapter),
    ("CMACGM", CmaCgmAdapter),
    ("ONE", OneAdapter),
    ("HMM", HmmAdapter),
    ("HAPAG", HapagLloydAdapter),
]

RESERVED = [
    CarrierInfo(
        slug="msc",
        name="MSC",
        code="MSCU",
        status="reserved",
        integration="official/public interface pending verification",
    ),
    CarrierInfo(
        slug="cosco",
        name="COSCO SHIPPING Lines",
        code="COSU",
        status="reserved",
        integration="official/public interface pending verification",
    ),
    CarrierInfo(
        slug="oocl",
        name="OOCL",
        code="OOLU",
        status="reserved",
        integration="official/public interface pending verification",
    ),
    CarrierInfo(
        slug="evergreen",
        name="Evergreen Marine",
        code="EGLV",
        status="reserved",
        integration="official/public interface pending verification",
    ),
]


def _enabled(prefix: str) -> bool:
    return os.getenv(f"{prefix}_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}


def get_enabled_adapters():
    adapters = []
    for prefix, adapter_cls in READY:
        if _enabled(prefix):
            adapter = adapter_cls()
            if adapter.configured and adapter.point_to_point_path:
                adapters.append(adapter)
    return adapters


def get_carriers() -> list[CarrierInfo]:
    carriers: list[CarrierInfo] = []
    for prefix, adapter_cls in READY:
        adapter = adapter_cls()
        carriers.append(
            CarrierInfo(
                slug=adapter.slug,
                name=adapter.name,
                code=adapter.code,
                status="ready" if _enabled(prefix) and adapter.configured and adapter.point_to_point_path else "disabled",
                integration="official schedule API",
            )
        )
    carriers.extend(RESERVED)
    return carriers
