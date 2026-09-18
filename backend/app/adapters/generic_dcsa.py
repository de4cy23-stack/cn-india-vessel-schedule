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


def _location_code(value: Any) -> str | None:
    if not isinstance(value, dict):
        return None

    location = value.get("location")
    if isinstance(location, dict):
        return (
            location.get("UNLocationCode")
            or location.get("unLocationCode")
            or location.get("locationCode")
        )

    return (
        value.get("UNLocationCode")
        or value.get("unLocationCode")
        or value.get("locationCode")
    )


def _event_dt(value: Any) -> datetime | None:
    if not isinstance(value, dict):
        return None
    return _parse_dt(
        value.get("dateTime")
        or value.get("eventDateTime")
        or value.get("departureDateTime")
        or value.get("arrivalDateTime")
    )


def _rows(payload: object) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]

    if not isinstance(payload, dict):
        return []

    for key in (
        "data",
        "routes",
        "schedules",
        "results",
        "products",
        "oceanProducts",
        "pointToPointRoutes",
    ):
        candidate = payload.get(key)
        if isinstance(candidate, list):
            return [x for x in candidate if isinstance(x, dict)]

    # Some providers return a single route object.
    if "legs" in payload or "placeOfReceipt" in payload:
        return [payload]

    return []


class GenericDcsaAdapter(CarrierAdapter):
    point_to_point_path: str = ""
    origin_param: str = "placeOfReceipt"
    destination_param: str = "placeOfDelivery"
    date_from_param: str | None = "departureStartDate"
    date_to_param: str | None = "departureEndDate"
    extra_params: dict[str, str]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extra_params = {}

    def build_params(
        self,
        origin: str,
        destination: str,
        date_from: date,
        date_to: date,
    ) -> dict[str, str]:
        params = {
            self.origin_param: origin,
            self.destination_param: destination,
        }
        if self.date_from_param:
            params[self.date_from_param] = date_from.isoformat()
        if self.date_to_param:
            params[self.date_to_param] = date_to.isoformat()
        params.update(self.extra_params)
        return params

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
            self.build_params(origin, destination, date_from, date_to),
        )
        return self.normalize(payload, origin, destination)

    def normalize(self, payload: object, origin: str, destination: str) -> list[Schedule]:
        output: list[Schedule] = []

        for row in _rows(payload):
            receipt = row.get("placeOfReceipt")
            delivery = row.get("placeOfDelivery")

            etd = _event_dt(receipt) or _parse_dt(
                row.get("departureDateTime")
                or row.get("departureTime")
                or row.get("etd")
            )
            eta = _event_dt(delivery) or _parse_dt(
                row.get("arrivalDateTime")
                or row.get("arrivalTime")
                or row.get("eta")
            )

            legs_payload = row.get("legs") if isinstance(row.get("legs"), list) else []
            legs: list[ScheduleLeg] = []
            vessel_leg_indexes: list[int] = []

            for i, leg in enumerate(legs_payload, start=1):
                if not isinstance(leg, dict):
                    continue

                departure = leg.get("departure") if isinstance(leg.get("departure"), dict) else {}
                arrival = leg.get("arrival") if isinstance(leg.get("arrival"), dict) else {}
                transport = leg.get("transport") if isinstance(leg.get("transport"), dict) else {}

                mode = str(
                    transport.get("modeOfTransport")
                    or leg.get("modeOfTransport")
                    or ""
                ).upper()

                vessel_data = transport.get("vessel")
                if not isinstance(vessel_data, dict):
                    vessel_data = {}

                vessel = (
                    vessel_data.get("name")
                    or vessel_data.get("vesselName")
                    or transport.get("vesselName")
                    or leg.get("vesselName")
                    or leg.get("vessel")
                )

                partners = transport.get("servicePartners")
                if not isinstance(partners, list):
                    partners = []

                partner = None
                for candidate in partners:
                    if not isinstance(candidate, dict):
                        continue
                    if str(candidate.get("carrierCode", "")).upper() == self.code.upper():
                        partner = candidate
                        break
                    if partner is None:
                        partner = candidate
                partner = partner or {}

                voyage = (
                    partner.get("carrierExportVoyageNumber")
                    or partner.get("carrierImportVoyageNumber")
                    or transport.get("carrierVoyageNumber")
                    or leg.get("voyageNumber")
                    or leg.get("voyage")
                )
                service = (
                    partner.get("carrierServiceName")
                    or partner.get("carrierServiceCode")
                    or transport.get("serviceName")
                    or transport.get("serviceCode")
                    or leg.get("serviceName")
                    or leg.get("serviceCode")
                )

                normalized = ScheduleLeg(
                    sequence=leg.get("sequenceNumber") or i,
                    pol=_location_code(departure) or leg.get("pol"),
                    pod=_location_code(arrival) or leg.get("pod"),
                    vessel=vessel,
                    voyage=voyage,
                    service=service,
                    etd=_event_dt(departure)
                    or _parse_dt(leg.get("departureDateTime") or leg.get("etd")),
                    eta=_event_dt(arrival)
                    or _parse_dt(leg.get("arrivalDateTime") or leg.get("eta")),
                )
                legs.append(normalized)

                if mode == "VESSEL" or vessel:
                    vessel_leg_indexes.append(len(legs) - 1)

            vessel_legs = [legs[i] for i in vessel_leg_indexes]
            first_vessel_leg = vessel_legs[0] if vessel_legs else (legs[0] if legs else None)
            last_vessel_leg = vessel_legs[-1] if vessel_legs else (legs[-1] if legs else None)

            if etd is None and first_vessel_leg:
                etd = first_vessel_leg.etd
            if eta is None and last_vessel_leg:
                eta = last_vessel_leg.eta

            transit_days = None
            raw_transit = row.get("transitTime")
            if isinstance(raw_transit, (int, float)):
                transit_days = float(raw_transit)
            elif etd and eta:
                transit_days = round((eta - etd).total_seconds() / 86400, 2)

            transshipment_ports: list[str] = []
            if len(vessel_legs) > 1:
                for leg in vessel_legs[:-1]:
                    if leg.pod and leg.pod not in {origin, destination} and leg.pod not in transshipment_ports:
                        transshipment_ports.append(leg.pod)

            output.append(
                Schedule(
                    carrier=self.name,
                    carrier_code=self.code,
                    origin=_location_code(receipt) or origin,
                    destination=_location_code(delivery) or destination,
                    vessel=first_vessel_leg.vessel if first_vessel_leg else row.get("vesselName"),
                    voyage=first_vessel_leg.voyage if first_vessel_leg else row.get("voyageNumber"),
                    service=first_vessel_leg.service if first_vessel_leg else row.get("serviceName"),
                    etd=etd,
                    eta=eta,
                    transit_days=transit_days,
                    direct=(len(vessel_legs) <= 1) if vessel_legs else None,
                    transshipment_ports=transshipment_ports,
                    legs=legs,
                    source="official_api",
                )
            )

        return output
