from app.adapters.registry import READY


def test_current_dcsa_point_to_point_carrier_set():
    codes = {adapter_cls().code for _, adapter_cls in READY}
    assert {
        "MAEU",
        "MSCU",
        "CMDU",
        "ONEY",
        "EGLV",
        "HDMU",
        "HLCU",
        "ZIMU",
        "YMLU",
    } <= codes


def test_dcsa_adapters_send_major_api_version_header(monkeypatch):
    monkeypatch.delenv("CMACGM_API_VERSION", raising=False)

    from app.adapters.configured import CmaCgmAdapter

    adapter = CmaCgmAdapter()
    assert adapter.extra_headers["API-Version"] == "1"
