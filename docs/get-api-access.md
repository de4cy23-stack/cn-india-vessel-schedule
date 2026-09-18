# Getting carrier API access

The application code can connect to the carrier APIs, but carrier credentials must be issued by the carrier or its developer portal. Do not scrape or bypass authentication.

## Fastest path to a live result

### 1. Maersk

Create/subscribe to an application in the Maersk Developer Portal and obtain the **Consumer Key** for Ocean Commercial Schedules.

Put it in `backend/.env`:

```env
MAERSK_ENABLED=true
MAERSK_API_KEY=your_consumer_key
```

The adapter already targets:

- Base URL: `https://api.maersk.com`
- Endpoint: `/products/ocean-products`
- Auth header: `Consumer-Key`
- Required routing parameters: `origin`, `destination`, `vesselOperatorCarrierCode`

### 2. CMA CGM

Subscribe to the DCSA Commercial Schedules API in the CMA CGM API Portal.

For public API-key access:

```env
CMACGM_ENABLED=true
CMACGM_API_KEY=your_key_id
CMACGM_API_KEY_HEADER=KeyId
```

For private OAuth2 access, configure client credentials instead:

```env
CMACGM_ENABLED=true
CMACGM_OAUTH_TOKEN_URL=https://auth.cma-cgm.com/as/token.oauth2
CMACGM_OAUTH_CLIENT_ID=...
CMACGM_OAUTH_CLIENT_SECRET=...
```

### 3. MSC / ONE / Evergreen / HMM / Hapag-Lloyd

These carriers have current DCSA Commercial Schedules Point-to-Point implementations, but the API host and credentials are supplied through each carrier's onboarding/developer portal. Fill the carrier-specific values in `backend/.env`.

Example:

```env
MSC_ENABLED=true
MSC_BASE_URL=https://<official-host-issued-by-msc>
MSC_API_KEY=...
```

Do not guess production hostnames.

## Live verification

After credentials are configured:

```bash
cd backend
python -m scripts.live_check --origin CNNGB --destination INNSA --weeks 4
```

Or test one carrier:

```bash
python -m scripts.live_check --carrier maersk --origin CNSHA --destination INMUN
```

The checker never prints secrets. For every carrier it shows:

- enabled/configured state
- authentication mode
- base URL and endpoint
- HTTP/authentication failure if present
- number of normalized schedules
- first vessel/voyage/ETD/ETA when successful

## What "run through" means

A carrier is considered fully live only after all four stages pass:

1. endpoint reachable
2. authentication accepted
3. schedule response returned
4. response normalized into vessel/voyage/ETD/ETA
