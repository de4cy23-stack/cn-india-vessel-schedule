from app.ports import resolve_port


def test_china_port_aliases():
    assert resolve_port("宁波") == "CNNGB"
    assert resolve_port("Shanghai") == "CNSHA"


def test_india_port_aliases():
    assert resolve_port("JNPT") == "INNSA"
    assert resolve_port("Nhava Sheva") == "INNSA"
    assert resolve_port("Mundra") == "INMUN"


def test_unlocode_passthrough():
    assert resolve_port("inmaa") == "INMAA"
