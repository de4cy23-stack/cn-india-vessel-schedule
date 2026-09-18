from __future__ import annotations

import os

from app.adapters.generic_dcsa import GenericDcsaAdapter


class EnvDcsaAdapter(GenericDcsaAdapter):
    env_prefix: str

    def __init__(self):
        prefix = self.env_prefix
        super().__init__(
            base_url=os.getenv(f"{prefix}_BASE_URL", ""),
            api_key=os.getenv(f"{prefix}_API_KEY", ""),
            api_key_header=os.getenv(f"{prefix}_API_KEY_HEADER", "Authorization"),
        )
        self.point_to_point_path = os.getenv(f"{prefix}_POINT_TO_POINT_PATH", "")


class MaerskAdapter(EnvDcsaAdapter):
    slug = "maersk"
    name = "Maersk"
    code = "MAEU"
    env_prefix = "MAERSK"


class CmaCgmAdapter(EnvDcsaAdapter):
    slug = "cma-cgm"
    name = "CMA CGM"
    code = "CMDU"
    env_prefix = "CMACGM"


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
