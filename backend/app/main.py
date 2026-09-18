from __future__ import annotations

import asyncio
from datetime import date, timedelta

from fastapi import FastAPI, HTTPException, Query

from app.adapters import get_carriers, get_enabled_adapters
from app.models import CarrierQueryStatus, Schedule, ScheduleSearchResponse
from app.ports import PORTS, resolve_port

app = FastAPI(
    title="CN-India Vessel Schedule Aggregator",
    version="0.2.0",
    description="Aggregate ETD/ETA schedules from multiple ocean carriers.",
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/ports")
async def ports():
    return PORTS


@app.get("/carriers")
async def carriers():
    return get_carriers()


async def _search(
    origin: str,
    destination: str,
    date_from: date,
    weeks: int,
) -> ScheduleSearchResponse:
    try:
        origin_code = resolve_port(origin)
        destination_code = resolve_port(destination)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    date_to = date_from + timedelta(weeks=weeks)
    adapters = get_enabled_adapters()

    if not adapters:
        return ScheduleSearchResponse(
            origin=origin_code,
            destination=destination_code,
            date_from=date_from,
            date_to=date_to,
            results=[],
            carriers=[],
        )

    batches = await asyncio.gather(
        *[
            adapter.search(origin_code, destination_code, date_from, date_to)
            for adapter in adapters
        ],
        return_exceptions=True,
    )

    results: list[Schedule] = []
    statuses: list[CarrierQueryStatus] = []

    for adapter, batch in zip(adapters, batches):
        if isinstance(batch, Exception):
            statuses.append(
                CarrierQueryStatus(
                    carrier=adapter.name,
                    code=adapter.code,
                    status="error",
                    count=0,
                    error=f"{type(batch).__name__}: {batch}",
                )
            )
            continue

        results.extend(batch)
        statuses.append(
            CarrierQueryStatus(
                carrier=adapter.name,
                code=adapter.code,
                status="ok",
                count=len(batch),
            )
        )

    results.sort(key=lambda item: (item.etd is None, item.etd))

    return ScheduleSearchResponse(
        origin=origin_code,
        destination=destination_code,
        date_from=date_from,
        date_to=date_to,
        results=results,
        carriers=statuses,
    )


@app.get("/search", response_model=ScheduleSearchResponse)
async def search(
    origin: str = Query(..., examples=["宁波", "CNNGB"]),
    destination: str = Query(..., examples=["Nhava Sheva", "INNSA"]),
    date_from: date = Query(default_factory=date.today),
    weeks: int = Query(4, ge=1, le=12),
):
    return await _search(origin, destination, date_from, weeks)


@app.get("/schedules", response_model=list[Schedule])
async def schedules(
    origin: str = Query(..., examples=["上海", "CNSHA"]),
    destination: str = Query(..., examples=["Mundra", "INMUN"]),
    date_from: date = Query(default_factory=date.today),
    weeks: int = Query(4, ge=1, le=12),
):
    response = await _search(origin, destination, date_from, weeks)
    return response.results
