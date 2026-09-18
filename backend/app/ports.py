from __future__ import annotations

import re


PORTS = [
    {"code": "CNNGB", "name": "Ningbo", "name_zh": "宁波", "country": "CN"},
    {"code": "CNSHA", "name": "Shanghai", "name_zh": "上海", "country": "CN"},
    {"code": "INNSA", "name": "Nhava Sheva / JNPT", "name_zh": "那瓦舍瓦", "country": "IN"},
    {"code": "INMUN", "name": "Mundra", "name_zh": "蒙德拉", "country": "IN"},
    {"code": "INMAA", "name": "Chennai", "name_zh": "金奈", "country": "IN"},
    {"code": "INPAV", "name": "Pipavav", "name_zh": "皮帕瓦沃", "country": "IN"},
    {"code": "INHZA", "name": "Hazira Port / Surat", "name_zh": "哈吉拉", "country": "IN"},
    {"code": "INCCU", "name": "Kolkata", "name_zh": "加尔各答", "country": "IN"},
]


ALIASES = {
    "NINGBO": "CNNGB",
    "宁波": "CNNGB",
    "寧波": "CNNGB",
    "SHANGHAI": "CNSHA",
    "上海": "CNSHA",
    "NHAVA SHEVA": "INNSA",
    "NHAVASHEVA": "INNSA",
    "JNPT": "INNSA",
    "JAWAHARLAL NEHRU": "INNSA",
    "JAWAHARLAL NEHRU PORT": "INNSA",
    "那瓦舍瓦": "INNSA",
    "纳瓦舍瓦": "INNSA",
    "MUNDRA": "INMUN",
    "蒙德拉": "INMUN",
    "CHENNAI": "INMAA",
    "MADRAS": "INMAA",
    "金奈": "INMAA",
    "PIPAVAV": "INPAV",
    "HAZIRA": "INHZA",
    "HAZIRA PORT": "INHZA",
    "KOLKATA": "INCCU",
    "CALCUTTA": "INCCU",
    "加尔各答": "INCCU",
}


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().upper().replace("-", " "))


def resolve_port(value: str) -> str:
    raw = value.strip()
    code = raw.upper().replace(" ", "")

    if re.fullmatch(r"[A-Z]{2}[A-Z0-9]{3}", code):
        return code

    normalized = _normalize(raw)
    if normalized in ALIASES:
        return ALIASES[normalized]

    raise ValueError(
        f"Unknown port '{value}'. Use a 5-character UN/LOCODE or one of the aliases from /ports."
    )
