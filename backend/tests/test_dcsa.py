from app.adapters.generic_dcsa import GenericDcsaAdapter


class DemoAdapter(GenericDcsaAdapter):
    slug = "demo"
    name = "Demo Carrier"
    code = "DEMO"


def test_dcsa_transshipment_route_normalization():
    adapter = DemoAdapter("https://example.invalid", "test")

    payload = [
        {
            "placeOfReceipt": {
                "location": {"UNLocationCode": "CNNGB"},
                "dateTime": "2026-09-22T10:00:00+08:00",
            },
            "placeOfDelivery": {
                "location": {"UNLocationCode": "INNSA"},
                "dateTime": "2026-10-11T15:00:00+05:30",
            },
            "transitTime": 19,
            "legs": [
                {
                    "sequenceNumber": 1,
                    "departure": {
                        "location": {"UNLocationCode": "CNNGB"},
                        "dateTime": "2026-09-22T10:00:00+08:00",
                    },
                    "arrival": {
                        "location": {"UNLocationCode": "SGSIN"},
                        "dateTime": "2026-09-27T08:00:00+08:00",
                    },
                    "transport": {
                        "modeOfTransport": "VESSEL",
                        "vessel": {"name": "FIRST VESSEL"},
                        "servicePartners": [
                            {
                                "carrierCode": "DEMO",
                                "carrierServiceName": "Asia Service",
                                "carrierExportVoyageNumber": "001W",
                            }
                        ],
                    },
                },
                {
                    "sequenceNumber": 2,
                    "departure": {
                        "location": {"UNLocationCode": "SGSIN"},
                        "dateTime": "2026-09-28T10:00:00+08:00",
                    },
                    "arrival": {
                        "location": {"UNLocationCode": "INNSA"},
                        "dateTime": "2026-10-11T15:00:00+05:30",
                    },
                    "transport": {
                        "modeOfTransport": "VESSEL",
                        "vessel": {"name": "SECOND VESSEL"},
                        "servicePartners": [
                            {
                                "carrierCode": "DEMO",
                                "carrierServiceName": "India Service",
                                "carrierExportVoyageNumber": "002W",
                            }
                        ],
                    },
                },
            ],
        }
    ]

    result = adapter.normalize(payload, "CNNGB", "INNSA")

    assert len(result) == 1
    schedule = result[0]
    assert schedule.origin == "CNNGB"
    assert schedule.destination == "INNSA"
    assert schedule.vessel == "FIRST VESSEL"
    assert schedule.voyage == "001W"
    assert schedule.transit_days == 19
    assert schedule.direct is False
    assert schedule.transshipment_ports == ["SGSIN"]
    assert schedule.etd is not None
    assert schedule.eta is not None
