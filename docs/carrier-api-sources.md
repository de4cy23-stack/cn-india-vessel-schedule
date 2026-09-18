# Carrier API source matrix

This project prefers official carrier APIs over website scraping.

| Carrier | Schedule source | Integration state | Notes |
|---|---|---|---|
| Maersk | Developer Portal - Ocean Commercial Schedules / Ocean Products | Adapter implemented | `GET https://api.maersk.com/products/ocean-products`; Consumer-Key; `vesselOperatorCarrierCode` required |
| CMA CGM | API Portal - DCSA Commercial Schedules | Adapter implemented | DCSA `GET /v1/point-to-point-routes`; production base `https://apis.cma-cgm.net` |
| ONE | ONE Developer Portal - Point-to-Point Schedule | Adapter implemented, endpoint supplied by subscription | DCSA compliant v1.0.9 |
| HMM | HMM API Portal - Port-to-Port Schedule | Adapter implemented, endpoint supplied by subscription | Portal documents a 300 calls/hour limit for Port-to-Port Schedule |
| Hapag-Lloyd | API Portal - Commercial Schedule | Adapter implemented, endpoint supplied by subscription | Official API credentials/endpoints required |
| MSC | MSC Developer Portal - DCSA Commercial Schedules | Adapter implemented, endpoint supplied by onboarding | MSC states Point-to-Point is live and DCSA compliant |
| COSCO | Official/public source still being validated | Reserved | Do not depend on an undocumented web endpoint |
| OOCL | Official/public source still being validated | Reserved | Do not depend on an undocumented web endpoint |
| Evergreen | DCSA Commercial Schedules 1.0 implementation | Adapter implemented, endpoint supplied by onboarding | DCSA lists Commercial Schedules 1.0 as implemented |

## Why DCSA is the internal model

DCSA Commercial Schedules defines point-to-point, port schedule and vessel schedule use cases. For point-to-point searches, the standardized route object contains estimated timing and transport legs, which lets this application normalize different carriers to the same fields:

- carrier
- vessel / voyage
- ETD / ETA
- transit time
- direct vs transshipment
- transshipment ports

## Credentials

Never commit carrier credentials. Put them in `backend/.env` or deployment secrets.

The HTTP layer supports:

1. API key headers.
2. A pre-issued Bearer token.
3. OAuth2 Client Credentials with automatic token caching and refresh.

CMA CGM documents public API authentication with the `KeyId` header and private API authentication using OAuth2 Client Credentials.
