from __future__ import annotations

import asyncio
from datetime import date, timedelta

from fastapi import FastAPI, Query

from app.adapters import get_carriers, get_enabled_adapters
from app.models import Schedule

app = FastAPI(
    title="CN-India Vessel Schedule Aggregator",
    version="0.1.0",
    description="Aggregate ETD/ETA schedules from multiple ocean carriers.",
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/carriers")
async def carriers():
    return get_carriers()


@app.get("/schedules", response_model=list[Schedule])
async def schedules(
    origin: str = Query(..., examples=["CNNGB"]),
    destination: str = Query(..., examples=["INNSA"]),
    date_from: date = Query(default_factory=date.today),
    weeks: int = Query(4, ge=1, le=12),
):
    date_to = date_from + timedelta(weeks=weeks)
    adapters = get_enabled_adapters()

    if not adapters:
        return []

    batches = await asyncio.gather(
        *[
            adapter.search(origin.upper(), destination.upper(), date_from, date_to)
            for adapter in adapters
        ],
        return_exceptions=True,
    )

    results: list[Schedule] = []
    for batch in batches:
        if isinstance(batch, Exception):
            continue
        results.extend(batch)

    results.sort(key=lambda x: (x.etd is None, x.etd))
    return results
