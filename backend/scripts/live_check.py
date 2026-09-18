from __future__ import annotations

import argparse
import asyncio
import os
from datetime import date, timedelta

import httpx

from app.adapters.registry import READY
from app.ports import resolve_port


def enabled(prefix: str) -> bool:
    return os.getenv(f"{prefix}_ENABLED", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def safe_http_error(exc: httpx.HTTPStatusError) -> str:
    response = exc.response
    text = (response.text or "").replace("\n", " ").strip()
    if len(text) > 300:
        text = text[:300] + "..."
    return f"HTTP {response.status_code}" + (f" - {text}" if text else "")


async def check_carrier(
    prefix: str,
    adapter_cls,
    origin: str,
    destination: str,
    date_from: date,
    date_to: date,
) -> bool:
    adapter = adapter_cls()
    is_enabled = enabled(prefix)

    print(f"\n[{adapter.name}]")
    print(f"  enabled: {is_enabled}")
    print(f"  configured: {adapter.configured}")
    print(f"  auth: {adapter.auth_mode}")
    print(f"  base_url: {adapter.base_url or '(missing)'}")
    print(f"  endpoint: {adapter.point_to_point_path or '(missing)'}")

    if not adapter.configured:
        print("  result: SKIP - credentials/base URL incomplete")
        return True

    try:
        results = await adapter.search(origin, destination, date_from, date_to)
    except httpx.HTTPStatusError as exc:
        print(f"  result: FAIL - {safe_http_error(exc)}")
        return False
    except httpx.RequestError as exc:
        print(f"  result: FAIL - network error: {type(exc).__name__}: {exc}")
        return False
    except Exception as exc:
        print(f"  result: FAIL - {type(exc).__name__}: {exc}")
        return False

    print(f"  result: OK - {len(results)} normalized schedules")
    if results:
        first = results[0]
        print(
            "  first: "
            f"{first.vessel or '-'} / {first.voyage or '-'} | "
            f"ETD={first.etd or '-'} | ETA={first.eta or '-'} | "
            f"direct={first.direct}"
        )
    return True


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Live-check configured carrier schedule APIs without printing secrets."
    )
    parser.add_argument("--origin", default="CNNGB")
    parser.add_argument("--destination", default="INNSA")
    parser.add_argument("--date-from", default=date.today().isoformat())
    parser.add_argument("--weeks", type=int, default=4)
    parser.add_argument(
        "--carrier",
        default="all",
        help="carrier prefix/slug/name fragment, or 'all'",
    )
    args = parser.parse_args()

    origin = resolve_port(args.origin)
    destination = resolve_port(args.destination)
    date_from = date.fromisoformat(args.date_from)
    date_to = date_from + timedelta(weeks=args.weeks)

    print(
        f"Live carrier API check: {origin} -> {destination}, "
        f"{date_from} to {date_to}"
    )
    print("Secrets are never printed.")

    checks = []
    needle = args.carrier.strip().lower()

    for prefix, adapter_cls in READY:
        adapter = adapter_cls()
        haystack = " ".join(
            [prefix, adapter.slug, adapter.name, adapter.code]
        ).lower()

        if needle != "all" and needle not in haystack:
            continue

        checks.append(
            check_carrier(
                prefix,
                adapter_cls,
                origin,
                destination,
                date_from,
                date_to,
            )
        )

    if not checks:
        print("No matching carrier.")
        return 2

    outcomes = await asyncio.gather(*checks)
    return 0 if all(outcomes) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
