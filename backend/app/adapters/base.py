from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

import httpx

from app.models import Schedule
from app.settings import REQUEST_TIMEOUT_SECONDS


class CarrierAdapter(ABC):
    slug: str
    name: str
    code: str
    integration: str = "official_api"

    def __init__(self, base_url: str, api_key: str = "", api_key_header: str = "Authorization"):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.api_key_header = api_key_header

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.api_key)

    def headers(self) -> dict[str, str]:
        if not self.api_key:
            return {}
        return {self.api_key_header: self.api_key}

    async def get_json(self, path: str, params: dict[str, str]) -> object:
        async with httpx.AsyncClient(
            base_url=self.base_url,
            timeout=REQUEST_TIMEOUT_SECONDS,
            headers=self.headers(),
        ) as client:
            response = await client.get(path, params=params)
            response.raise_for_status()
            return response.json()

    @abstractmethod
    async def search(
        self,
        origin: str,
        destination: str,
        date_from: date,
        date_to: date,
    ) -> list[Schedule]:
        raise NotImplementedError

    @abstractmethod
    def normalize(self, payload: object, origin: str, destination: str) -> list[Schedule]:
        raise NotImplementedError
