# Daily Automation Setup Guide

This guide explains how to set up the daily automation system that:
1. Syncs new announcements from Base.gov.pt API (incremental updates)
2. Filters announcements based on saved search criteria
3. Automatically creates HubSpot deals for matching announcements

## Architecture

The automation runs daily via **GitHub Actions** (free for public repositories) and:
- Only fetches new announcements (incremental, not full year sync)
- Uses your saved searches from the Streamlit app for filtering
- Tracks processed announcements to avoid duplicates
- Logs all operations for monitoring

## Setup Steps

### 1. Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:

- **`BASE_API_KEY`**: Your Base.gov.pt API token
  - Value: Your API key (e.g., `3ovhOk63uVC3XJt6FdqN`)

- **`HUBSPOT_API_TOKEN`**: Your HubSpot Private App Access Token
  - Value: Your HubSpot token (e.g., `pat-eu1-...`)

- **`AUTOMATION_SAVED_SEARCH`** (optional): Name of saved search to use
  - Default: `"Default Automation"`
  - Value: The exact name of a saved search you created in the Streamlit app

- **`DAYS_TO_CHECK`** (optional): How many days back to check
  - Default: `"1"` (yesterday only)
  - Value: `"1"`, `"2"`, `"7"`, etc.

### 2. Create a Saved Search in the App

1. Open your Streamlit app
2. Configure filters (CPV codes, keywords, location, etc.)
3. Click "Save Search" in the sidebar
4. Give it a name (e.g., "Default Automation")
5. This name must match `AUTOMATION_SAVED_SEARCH` secret (or use default)

### 3. Verify HubSpot Deal Properties

Make sure all required HubSpot deal properties exist. The automation creates deals with these properties:

- `dealname` (default)
- `dealstage` (default: "appointmentscheduled")
- `pipeline` (default: "default")
- `ver_anuncio` (URL to view announcement)
- `documentos` (URL to documents)
- `numero_de_anuncio` (announcement number)
- `prazo_de_submissao` (deadline)
- `descricao_do_procedimento` (description)
- `tipo` (procedure type)
- `codigos_cpv` (CPV codes)
- `entidade_contratante` (contracting entity)
- `data_de_publicacao` (publication date - timestamp)
- `preco_eur` (base price in EUR)

If you haven't created these properties yet, run the HubSpot property creation script first.

### 4. Test Locally (Optional)

Before enabling GitHub Actions, test the script locally:

```bash
# Set environment variables
export BASE_API_KEY="your_base_api_key"
export HUBSPOT_API_TOKEN="your_hubspot_token"
export AUTOMATION_SAVED_SEARCH="Default Automation"

# Run the script
python daily_automation.py
```

### 5. Enable GitHub Actions

1. Push the code to GitHub (the workflow file is already in `.github/workflows/daily-sync.yml`)
2. Go to your repository → Actions tab
3. The workflow will run automatically at 5:30 PM UTC daily (6:30 PM Portugal time)
4. You can also trigger it manually: Actions → Daily Portal Base Sync → Run workflow

## How It Works

### Daily Execution Flow

1. **Fetch New Announcements** (5:30 PM UTC daily)
   - Fetches announcements from Base.gov.pt API for yesterday (or configured date range)
   - Only stores announcements not already in cache (incremental)

2. **Apply Filters**
   - Loads your saved search filters
   - Filters announcements based on CPV codes, keywords, location, etc.

3. **Create HubSpot Deals**
   - For each matching announcement:
     - Checks if already processed (database check)
     - Checks if deal exists in HubSpot (API check)
     - Creates new deal if not found
     - Marks announcement as processed

4. **Logging**
   - All operations logged to `daily_sync_log` table
   - Summary printed to GitHub Actions logs

### Database Tables

The automation uses these new database tables:

- **`processed_announcements`**: Tracks which announcements have been processed
  - `n_anuncio`: Announcement number (primary key)
  - `processed_at`: When it was processed
  - `hubspot_deal_id`: HubSpot deal ID if created
  - `saved_search_name`: Which saved search was used

- **`daily_sync_log`**: Daily operation logs
  - `sync_date`: Date of sync
  - `announcements_fetched`: Total fetched from API
  - `announcements_new`: New announcements added
  - `deals_created`: Successfully created deals
  - `deals_failed`: Failed deal creations
  - `sync_status`: "success", "partial", or "error"

## Monitoring

### View Logs

1. **GitHub Actions**: Go to Actions tab → Click on latest run → View logs
2. **Database**: Query `daily_sync_log` table for history

### Check Status

The automation logs include:
- Number of announcements fetched
- Number of new announcements
- Number matching filters
- Number of deals created/failed
- Any errors encountered

## Troubleshooting

### "Saved search not found"

- Make sure you created a saved search in the Streamlit app
- Check that the name matches `AUTOMATION_SAVED_SEARCH` secret (case-sensitive)
- List available searches in the error message

### "HubSpot API token not found"

- Verify `HUBSPOT_API_TOKEN` secret is set in GitHub
- Check that the token is valid and has deal creation permissions

### "No deals created"

- Check that announcements match your saved search filters
- Verify HubSpot deal properties exist
- Check GitHub Actions logs for specific error messages

### Database not persisting

- GitHub Actions uses ephemeral storage
- The database is recreated on each run
- This is fine - the automation checks HubSpot API for existing deals
- Consider using external database (Supabase, etc.) for persistent storage if needed

## Customization

### Change Schedule

Edit `.github/workflows/daily-sync.yml`:

```yaml
schedule:
  - cron: '30 17 * * *'  # 5:30 PM UTC daily
```

Use [crontab.guru](https://crontab.guru) to generate cron expressions.

### Change Date Range

Set `DAYS_TO_CHECK` secret to check more days:
- `"1"`: Yesterday only (default)
- `"7"`: Last 7 days
- `"30"`: Last 30 days

### Multiple Saved Searches

You can create multiple workflows for different saved searches by:
1. Duplicating `.github/workflows/daily-sync.yml`
2. Renaming it (e.g., `daily-sync-healthcare.yml`)
3. Setting different `AUTOMATION_SAVED_SEARCH` secret or hardcoding the name

## Files Created

- `daily_automation.py`: Main automation script
- `hubspot_automation.py`: HubSpot integration module
- `filter_utils.py`: Reusable filtering logic
- `.github/workflows/daily-sync.yml`: GitHub Actions workflow
- Updated `cached_api_client.py`: Added incremental sync and tracking methods
- Updated `config.py`: Added HubSpot token management

## Next Steps

1. ✅ Set up GitHub secrets
2. ✅ Create saved search in Streamlit app
3. ✅ Verify HubSpot properties exist
4. ✅ Push code to GitHub
5. ✅ Monitor first run in GitHub Actions
6. ✅ Check HubSpot for created deals

## Support

If you encounter issues:
1. Check GitHub Actions logs for detailed error messages
2. Verify all secrets are correctly set
3. Test locally first to isolate issues
4. Check that saved search exists and has filters configured

