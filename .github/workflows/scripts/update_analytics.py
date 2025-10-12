#!/usr/bin/env python3
"""
Quick analytics update script for Hugo build process
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

def update_analytics_update():
    """Quick analytics update with minimal dependencies"""
    try:
        # Check if required environment variables are set
        if not os.environ.get('GOOGLE_SERVICE_ACCOUNT_KEY'):
            print("⚠️  GOOGLE_SERVICE_ACCOUNT_KEY not set - skipping analytics update")
            return
        
        if not os.environ.get('GOOGLE_ANALYTICS_PROPERTY_ID'):
            print("⚠️  GOOGLE_ANALYTICS_PROPERTY_ID not set - skipping analytics update")
            return
        
        # Import Google Analytics libraries
        try:
            from google.analytics.data_v1beta import BetaAnalyticsDataClient
            from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Metric
            from google.oauth2 import service_account
        except ImportError as e:
            print(f"⚠️  Google Analytics libraries not available: {e}")
            print("Skipping analytics update")
            return
        
        # Setup authentication
        credentials_info = json.loads(os.environ['GOOGLE_SERVICE_ACCOUNT_KEY'])
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=['https://www.googleapis.com/auth/analytics.readonly']
        )
        
        # Initialize the client
        client = BetaAnalyticsDataClient(credentials=credentials)
        property_id = os.environ['GOOGLE_ANALYTICS_PROPERTY_ID']
        
        print("🔄 Fetching analytics data...")
        
        # Build the request
        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
            metrics=[
                Metric(name="screenPageViews"),
                Metric(name="totalUsers"),
                Metric(name="sessions"),
            ],
        )
        
        # Run the report
        response = client.run_report(request=request)
        
        # Extract data
        if response.rows:
            row = response.rows[0]
            views = int(row.metric_values[0].value) if row.metric_values else 0
            users = int(row.metric_values[1].value) if len(row.metric_values) > 1 else 0
            sessions = int(row.metric_values[2].value) if len(row.metric_values) > 2 else 0
        else:
            views = users = sessions = 0
        
        # Prepare data
        data = {
            "lastUpdated": datetime.now().isoformat(),
            "period": "Last 30 days",
            "metrics": {
                "totalPageViews": views,
                "totalUsers": users,
                "totalSessions": sessions
            },
            "formatted": {
                "totalPageViews": f"{views:,}",
                "totalUsers": f"{users:,}",
                "totalSessions": f"{sessions:,}"
            },
            "metadata": {
                "source": "Quick fetch during Hugo build"
            }
        }
        
        # Ensure data directory exists
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        # Write data
        analytics_file = data_dir / "analytics.json"
        with open(analytics_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Quick analytics update: {views:,} views, {users:,} users, {sessions:,} sessions")
        
    except Exception as error:
        print(f"⚠️  Analytics update failed: {error}")
        # Don't fail the build - just skip analytics update
        return False
    
    return True

if __name__ == "__main__":
    success = update_analytics_update()
    sys.exit(0)  # Always exit successfully to not break the build