# Analytics Setup Guide

This guide explains how to set up automated analytics data collection for your Hugo site using GitHub Actions and Google Analytics 4.

## 🎯 What This Setup Provides

- **Automated Data Collection**: Fetches analytics data weekly (configurable)
- **Two Simple Trigger Methods**: 
  1. **Scheduled**: Weekly (configurable cron schedule)
  2. **Manual**: Run workflow button for immediate updates
- **Secure**: API keys stored in GitHub Secrets, never exposed in code
- **Independent**: Analytics updates don't affect site deployment speed
- **Displays**: Total page views, users, sessions, top countries, popular pages

## 📋 Prerequisites

1. **Google Analytics 4** property set up on your website
2. **Google Cloud Project** with Analytics Reporting API enabled
3. **Service Account** with analytics read permissions
4. **GitHub Repository** with Actions enabled

## 🔧 Setup Instructions

### Step 1: Create Google Cloud Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select or create a project
3. Enable the **Google Analytics Reporting API**:
   - Go to "APIs & Services" → "Library"
   - Search for "Google Analytics Reporting API"
   - Click "Enable"

4. Create a Service Account:
   - Go to "IAM & Admin" → "Service Accounts"
   - Click "Create Service Account"
   - Name: `hugo-analytics-reader`
   - Description: `Read-only access to Google Analytics for Hugo site`
   - Click "Create and Continue"

5. Generate Service Account Key:
   - Click on the created service account
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key"
   - Choose "JSON" format
   - Download and save the JSON file securely

### Step 2: Grant Analytics Access

1. Go to [Google Analytics](https://analytics.google.com/)
2. Navigate to your property
3. Go to "Admin" (gear icon)
4. Under "Property", click "Property Access Management"
5. Click "+" to add users
6. Add the service account email (from the JSON file: `client_email`)
7. Set role to "Viewer"
8. Click "Add"

### Step 3: Get Analytics Property ID

1. In Google Analytics, go to "Admin"
2. Under "Property", note your Property ID (format: 123456789)
3. Or find it in the URL: `https://analytics.google.com/analytics/web/#/p123456789/`

### Step 4: Configure GitHub Secrets

1. Go to your GitHub repository
2. Navigate to "Settings" → "Secrets and variables" → "Actions"
3. Click "New repository secret" and add:

#### GOOGLE_SERVICE_ACCOUNT_KEY
- **Name**: `GOOGLE_SERVICE_ACCOUNT_KEY`
- **Value**: The entire contents of the JSON file you downloaded (copy and paste the whole JSON)

#### GOOGLE_ANALYTICS_PROPERTY_ID
- **Name**: `GOOGLE_ANALYTICS_PROPERTY_ID` 
- **Value**: Your Property ID (just the numbers, e.g., `123456789`)

### Step 5: Test the Setup

1. Go to "Actions" tab in your GitHub repository
2. Find "Update Analytics Data" workflow
3. Click "Run workflow" → "Run workflow" (manual trigger)
4. Wait for completion and check if `data/analytics.json` was created/updated

## 📊 Using Analytics in Your Hugo Site

### Basic Usage
Add analytics to any page or post:
```markdown
{{< analytics-stats >}}
```

### Display Options
```markdown
<!-- Show just summary metrics -->
{{< analytics-stats type="summary" >}}

<!-- Show top countries -->
{{< analytics-stats type="countries" >}}

<!-- Show popular pages -->
{{< analytics-stats type="pages" >}}

<!-- Show everything -->
{{< analytics-stats type="all" >}}
```

### Home Page Integration
Add to your `content/_index.md` or home page template:
```markdown
# Welcome to My Blog

{{< analytics-stats type="summary" >}}

<!-- Rest of your content -->
```

## ⚙️ Configuration Options

### Change Update Frequency
Edit `.github/workflows/update-analytics.yml` line 6-8:
```yaml
schedule:
  # Change this cron expression:
  # Weekly (default): '0 2 * * 0' (Sunday 2 AM)
  # Daily: '0 2 * * *'  (Every day 2 AM)
  # Bi-weekly: '0 2 */14 * *' (Every 14 days)
  # Monthly: '0 2 1 * *' (1st of month)
  - cron: '0 2 * * 0'
```

### Manual Updates
If you need fresh analytics before a big announcement:
1. Go to repository "Actions" tab
2. Select "Update Analytics Data" workflow  
3. Click "Run workflow" → Check "Force update" if needed
4. Wait ~2 minutes for completion
5. Your next Hugo deployment will use the fresh data

### Customize Data Collection
Edit the analytics fetcher script in `update-analytics.yml` to:
- Change date ranges (currently 30 days)
- Add more metrics
- Modify country/page limits
- Add custom dimensions

## 🔍 Data Structure

The generated `data/analytics.json` contains:
```json
{
  "lastUpdated": "2025-10-12T10:30:00Z",
  "period": "Last 30 days",
  "metrics": {
    "totalPageViews": 1234,
    "totalUsers": 567,
    "totalSessions": 890
  },
  "formatted": {
    "totalPageViews": "1,234",
    "totalUsers": "567", 
    "totalSessions": "890"
  },
  "topCountries": [
    {"country": "Australia", "users": 200, "percentage": 35.3}
  ],
  "topPages": [
    {"path": "/posts/popular-post/", "title": "Popular Post", "views": 150}
  ]
}
```

## 🐛 Troubleshooting

### Analytics not updating?
1. Check GitHub Actions logs for errors
2. Verify secrets are correctly set
3. Ensure service account has Analytics access
4. Check if API quota is exceeded

### No data showing?
1. Verify `data/analytics.json` exists
2. Check if Hugo can read the data file
3. Ensure shortcode syntax is correct
4. Check browser console for errors

### Permission errors?
1. Verify service account email is added to Analytics property
2. Ensure "Viewer" role is assigned
3. Check if the Property ID is correct
4. Confirm Analytics Reporting API is enabled

## 🔐 Security Notes

- ✅ API keys are stored in GitHub Secrets (encrypted)
- ✅ Keys never appear in code or logs
- ✅ Service account has minimal read-only permissions
- ✅ Generated data contains no sensitive information
- ✅ Works with static site hosting (no server required)

## 📝 Manual Updates

You can trigger analytics updates manually:
1. Go to repository "Actions" tab
2. Select "Update Analytics Data" workflow  
3. Click "Run workflow"
4. Wait for completion

Or set up local development:
```bash
# Set environment variables
export GOOGLE_SERVICE_ACCOUNT_KEY='{"type": "service_account"...}'
export GOOGLE_ANALYTICS_PROPERTY_ID='123456789'

# Run the update script
node .github/workflows/fetch-analytics.js
```

## 🚀 Next Steps

1. **Customize styling**: Modify the CSS in `analytics-stats.html`
2. **Add more metrics**: Extend the data collection script
3. **Create dashboards**: Build dedicated analytics pages
4. **Set up alerts**: Monitor significant changes in traffic
5. **Automate reports**: Generate weekly/monthly summaries

Need help? Check the GitHub Actions logs or create an issue in your repository.