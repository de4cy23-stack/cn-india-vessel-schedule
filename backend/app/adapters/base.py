from __future__ import annotations

import asyncio
import time
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

    def __init__(
        self,
        base_url: str,
        api_key: str = "",
        api_key_header: str = "Authorization",
        bearer_token: str = "",
        oauth_token_url: str = "",
        oauth_client_id: str = "",
        oauth_client_secret: str = "",
        oauth_scope: str = "",
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.api_key_header = api_key_header
        self.bearer_token = bearer_token
        self.oauth_token_url = oauth_token_url
        self.oauth_client_id = oauth_client_id
        self.oauth_client_secret = oauth_client_secret
        self.oauth_scope = oauth_scope

        self._cached_access_token = ""
        self._cached_access_token_expires_at = 0.0

    @property
    def configured(self) -> bool:
        auth_configured = bool(
            self.api_key
            or self.bearer_token
            or (
                self.oauth_token_url
                and self.oauth_client_id
                and self.oauth_client_secret
            )
        )
        return bool(self.base_url and auth_configured)

    async def _oauth_access_token(self) -> str:
        if self.bearer_token:
            return self.bearer_token

        if not (
            self.oauth_token_url
            and self.oauth_client_id
            and self.oauth_client_secret
        ):
            return ""

        now = time.monotonic()
        if self._cached_access_token and now < self._cached_access_token_expires_at:
            return self._cached_access_token

        data = {
            "grant_type": "client_credentials",
            "client_id": self.oauth_client_id,
            "client_secret": self.oauth_client_secret,
        }
        if self.oauth_scope:
            data["scope"] = self.oauth_scope

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(
                self.oauth_token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            payload = response.json()

        token = payload.get("access_token")
        if not isinstance(token, str) or not token:
            raise RuntimeError("OAuth2 token response does not contain access_token")

        expires_in = payload.get("expires_in", 300)
        try:
            ttl = max(float(expires_in) - 30.0, 30.0)
        except (TypeError, ValueError):
            ttl = 270.0

        self._cached_access_token = token
        self._cached_access_token_expires_at = time.monotonic() + ttl
        return token

    async def headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Accept": "application/json"}

        if self.api_key:
            headers[self.api_key_header] = self.api_key

        token = await self._oauth_access_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"

        return headers

    async def get_json(self, path: str, params: dict[str, str]) -> object:
        headers = await self.headers()

        async with httpx.AsyncClient(
            base_url=self.base_url,
            timeout=REQUEST_TIMEOUT_SECONDS,
            headers=headers,
        ) as client:
            for attempt in range(3):
                response = await client.get(path, params=params)

                if response.status_code not in {429, 500, 502, 503, 504}:
                    response.raise_for_status()
                    return response.json()

                if attempt == 2:
                    response.raise_for_status()

                retry_after = response.headers.get("Retry-After")
                try:
                    delay = min(float(retry_after), 60.0) if retry_after else 2 ** attempt
                except ValueError:
                    delay = 2 ** attempt

                await asyncio.sleep(delay)

        raise RuntimeError("Carrier request failed without a response")

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
