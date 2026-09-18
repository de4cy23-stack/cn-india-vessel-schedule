from __future__ import annotations

import os

from app.adapters.configured import (
    CmaCgmAdapter,
    EvergreenAdapter,
    HapagLloydAdapter,
    HmmAdapter,
    MaerskAdapter,
    MscAdapter,
    OneAdapter,
    YangMingAdapter,
    ZimAdapter,
)
from app.models import CarrierInfo


READY = [
    ("MAERSK", MaerskAdapter),
    ("MSC", MscAdapter),
    ("CMACGM", CmaCgmAdapter),
    ("ONE", OneAdapter),
    ("EVERGREEN", EvergreenAdapter),
    ("HMM", HmmAdapter),
    ("HAPAG", HapagLloydAdapter),
    ("ZIM", ZimAdapter),
    ("YANGMING", YangMingAdapter),
]

RESERVED = [
    CarrierInfo(
        slug="cosco",
        name="COSCO SHIPPING Lines",
        code="COSU",
        status="reserved",
        integration="official website schedule; stable API access not yet verified",
        configured=False,
    ),
    CarrierInfo(
        slug="oocl",
        name="OOCL",
        code="OOLU",
        status="reserved",
        integration="official website schedule; stable API access not yet verified",
        configured=False,
    ),
]


def _enabled(prefix: str) -> bool:
    return os.getenv(f"{prefix}_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}


def get_enabled_adapters():
    adapters = []
    for prefix, adapter_cls in READY:
        adapter = adapter_cls()
        if _enabled(prefix) and adapter.configured and adapter.point_to_point_path:
            adapters.append(adapter)
    return adapters


def get_carriers() -> list[CarrierInfo]:
    carriers: list[CarrierInfo] = []

    for prefix, adapter_cls in READY:
        adapter = adapter_cls()
        configured = bool(adapter.configured and adapter.point_to_point_path)
        carriers.append(
            CarrierInfo(
                slug=adapter.slug,
                name=adapter.name,
                code=adapter.code,
                status="ready" if configured else "disabled",
                integration="official schedule API",
                configured=configured,
            )
        )

    carriers.extend(RESERVED)
    return carriers
