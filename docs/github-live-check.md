# GitHub Actions live API check

The repository includes a manual workflow named **Live carrier API check**.

It is intentionally not scheduled because live schedule APIs consume carrier quotas.

## Add credentials safely

In GitHub:

1. Open the repository.
2. Go to **Settings → Secrets and variables → Actions**.
3. Add only the secrets for carriers you have access to.
4. Open **Actions → Live carrier API check → Run workflow**.
5. Enter an origin/destination such as `CNNGB` → `INNSA`.

Do not commit credentials to `.env.example`, source files, issues, or pull requests.

### Minimum useful secrets

For Maersk:

- `MAERSK_API_KEY`

For CMA CGM public API-key access:

- `CMACGM_API_KEY`

For providers where onboarding supplies a gateway URL:

- `<CARRIER>_BASE_URL`
- plus one of API key, Bearer token, or OAuth2 client credentials

OAuth2 secret names follow:

- `<CARRIER>_OAUTH_TOKEN_URL`
- `<CARRIER>_OAUTH_CLIENT_ID`
- `<CARRIER>_OAUTH_CLIENT_SECRET`

The workflow does not print credential values.
