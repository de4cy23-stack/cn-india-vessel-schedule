from __future__ import annotations

import os

from app.adapters.generic_dcsa import GenericDcsaAdapter


class EnvDcsaAdapter(GenericDcsaAdapter):
    env_prefix: str
    default_base_url: str = ""
    default_path: str = ""
    default_origin_param: str = "placeOfReceipt"
    default_destination_param: str = "placeOfDelivery"
    default_date_from_param: str = "departureStartDate"
    default_date_to_param: str = "departureEndDate"

    def __init__(self):
        prefix = self.env_prefix
        super().__init__(
            base_url=os.getenv(f"{prefix}_BASE_URL", self.default_base_url),
            api_key=os.getenv(f"{prefix}_API_KEY", ""),
            api_key_header=os.getenv(f"{prefix}_API_KEY_HEADER", "Authorization"),
        )

        self.point_to_point_path = os.getenv(
            f"{prefix}_POINT_TO_POINT_PATH",
            self.default_path,
        )
        self.origin_param = os.getenv(
            f"{prefix}_ORIGIN_PARAM",
            self.default_origin_param,
        )
        self.destination_param = os.getenv(
            f"{prefix}_DESTINATION_PARAM",
            self.default_destination_param,
        )

        date_from = os.getenv(f"{prefix}_DATE_FROM_PARAM", self.default_date_from_param)
        date_to = os.getenv(f"{prefix}_DATE_TO_PARAM", self.default_date_to_param)
        self.date_from_param = date_from or None
        self.date_to_param = date_to or None


class MaerskAdapter(EnvDcsaAdapter):
    slug = "maersk"
    name = "Maersk"
    code = "MAEU"
    env_prefix = "MAERSK"
    default_base_url = "https://api.maersk.com"
    default_path = "/products/ocean-products"
    default_origin_param = "origin"
    default_destination_param = "destination"
    # Maersk's Ocean Products endpoint is not a byte-for-byte DCSA endpoint.
    # Date parameter names are configurable because API product versions differ.
    default_date_from_param = ""
    default_date_to_param = ""

    def __init__(self):
        super().__init__()
        self.extra_params["vesselOperatorCarrierCode"] = os.getenv(
            "MAERSK_CARRIER_CODE",
            self.code,
        )


class CmaCgmAdapter(EnvDcsaAdapter):
    slug = "cma-cgm"
    name = "CMA CGM"
    code = "CMDU"
    env_prefix = "CMACGM"
    default_base_url = "https://apis.cma-cgm.net"
    default_path = "/v1/point-to-point-routes"


class OneAdapter(EnvDcsaAdapter):
    slug = "one"
    name = "Ocean Network Express (ONE)"
    code = "ONEY"
    env_prefix = "ONE"


class HmmAdapter(EnvDcsaAdapter):
    slug = "hmm"
    name = "HMM"
    code = "HDMU"
    env_prefix = "HMM"


class HapagLloydAdapter(EnvDcsaAdapter):
    slug = "hapag-lloyd"
    name = "Hapag-Lloyd"
    code = "HLCU"
    env_prefix = "HAPAG"
