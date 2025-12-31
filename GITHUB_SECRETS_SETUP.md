# GitHub Secrets Setup

## Required Secrets

Go to: `Settings → Secrets and variables → Actions`

| Secret | Description |
|--------|-------------|
| `BASE_API_KEY` | Base.gov.pt API token |
| `HUBSPOT_API_TOKEN` | HubSpot private app token |
| `AUTOMATION_SAVED_SEARCH` | Saved search name (default: `Biogerm`) |

## HubSpot Token Permissions

Required scopes for the HubSpot private app:
- `crm.objects.deals.read`
- `crm.objects.deals.write`
- `crm.objects.companies.read`
- `crm.objects.companies.write`

## Verification

1. Go to `Actions` tab in GitHub
2. Click "Daily Portal Base Sync"
3. Click "Run workflow" to test manually
4. Check logs for success messages
