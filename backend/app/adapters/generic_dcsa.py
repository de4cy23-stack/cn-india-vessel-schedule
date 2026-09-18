from __future__ import annotations

from datetime import date, datetime
from typing import Any

from app.adapters.base import CarrierAdapter
from app.models import Schedule, ScheduleLeg


def _parse_dt(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


class GenericDcsaAdapter(CarrierAdapter):
    point_to_point_path: str = ""

    async def search(
        self,
        origin: str,
        destination: str,
        date_from: date,
        date_to: date,
    ) -> list[Schedule]:
        if not self.point_to_point_path:
            return []

        payload = await self.get_json(
            self.point_to_point_path,
            {
                "placeOfReceipt": origin,
                "placeOfDelivery": destination,
                "departureStartDate": date_from.isoformat(),
                "departureEndDate": date_to.isoformat(),
            },
        )
        return self.normalize(payload, origin, destination)

    def normalize(self, payload: object, origin: str, destination: str) -> list[Schedule]:
        # DCSA implementations differ slightly by version/provider. This normalizer
        # deliberately accepts common response shapes and can be specialized per carrier.
        rows: list[dict[str, Any]]
        if isinstance(payload, list):
            rows = [x for x in payload if isinstance(x, dict)]
        elif isinstance(payload, dict):
            candidate = (
                payload.get("data")
                or payload.get("routes")
                or payload.get("schedules")
                or payload.get("results")
                or []
            )
            rows = [x for x in candidate if isinstance(x, dict)] if isinstance(candidate, list) else []
        else:
            rows = []

        output: list[Schedule] = []
        for row in rows:
            vessel = row.get("vesselName") or row.get("vessel")
            voyage = row.get("voyageNumber") or row.get("voyage")
            service = row.get("serviceName") or row.get("serviceCode") or row.get("service")

            etd = _parse_dt(
                row.get("departureDateTime")
                or row.get("departureTime")
                or row.get("etd")
            )
            eta = _parse_dt(
                row.get("arrivalDateTime")
                or row.get("arrivalTime")
                or row.get("eta")
            )

            legs_payload = row.get("legs") if isinstance(row.get("legs"), list) else []
            legs: list[ScheduleLeg] = []
            for leg in legs_payload:
                if not isinstance(leg, dict):
                    continue
                legs.append(
                    ScheduleLeg(
                        pol=leg.get("placeOfReceipt") or leg.get("pol"),
                        pod=leg.get("placeOfDelivery") or leg.get("pod"),
                        vessel=leg.get("vesselName") or leg.get("vessel"),
                        voyage=leg.get("voyageNumber") or leg.get("voyage"),
                        etd=_parse_dt(leg.get("departureDateTime") or leg.get("etd")),
                        eta=_parse_dt(leg.get("arrivalDateTime") or leg.get("eta")),
                    )
                )

            transit_days = None
            if etd and eta:
                transit_days = round((eta - etd).total_seconds() / 86400, 2)

            transshipment_ports = []
            for leg in legs[:-1]:
                if leg.pod and leg.pod not in {origin, destination}:
                    transshipment_ports.append(leg.pod)

            output.append(
                Schedule(
                    carrier=self.name,
                    carrier_code=self.code,
                    origin=origin,
                    destination=destination,
                    vessel=vessel,
                    voyage=voyage,
                    service=service,
                    etd=etd,
                    eta=eta,
                    transit_days=transit_days,
                    direct=(len(legs) <= 1) if legs else None,
                    transshipment_ports=transshipment_ports,
                    legs=legs,
                    source="official_api",
                )
            )
        return output
