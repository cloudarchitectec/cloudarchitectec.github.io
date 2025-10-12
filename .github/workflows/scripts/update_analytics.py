#!/usr/bin/env python3
"""
Quick analytics update script for Hugo build process
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

def quick_analytics_update():
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
            from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Metric, Dimension, OrderBy
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
        
        # Build the request for main metrics
        main_request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
            metrics=[
                Metric(name="screenPageViews"),
                Metric(name="totalUsers"),
                Metric(name="sessions"),
            ],
        )
        
        # Build the request for top pages
        pages_request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
            metrics=[Metric(name="screenPageViews")],
            dimensions=[
                Dimension(name="pagePath"),
                Dimension(name="pageTitle")
            ],
            order_bys=[OrderBy(
                metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"),
                desc=True
            )],
            limit=10,
        )
        
        # Build the request for top countries
        countries_request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
            metrics=[Metric(name="totalUsers")],
            dimensions=[Dimension(name="country")],
            order_bys=[OrderBy(
                metric=OrderBy.MetricOrderBy(metric_name="totalUsers"),
                desc=True
            )],
            limit=10,
        )
        
        # Run the reports
        main_response = client.run_report(request=main_request)
        pages_response = client.run_report(request=pages_request)
        countries_response = client.run_report(request=countries_request)
        
        # Extract main metrics data
        if main_response.rows:
            row = main_response.rows[0]
            views = int(row.metric_values[0].value) if row.metric_values else 0
            users = int(row.metric_values[1].value) if len(row.metric_values) > 1 else 0
            sessions = int(row.metric_values[2].value) if len(row.metric_values) > 2 else 0
        else:
            views = users = sessions = 0
        
        # Extract top pages data
        top_pages = []
        if pages_response.rows:
            for row in pages_response.rows:
                if row.dimension_values and row.metric_values:
                    path = row.dimension_values[0].value
                    title = row.dimension_values[1].value if len(row.dimension_values) > 1 else "Unknown"
                    page_views = int(row.metric_values[0].value)
                    
                    # Only include actual blog posts (filter out homepage, search, etc.)
                    if path.startswith('/posts/') and not path.endswith('/'):
                        top_pages.append({
                            "path": path,
                            "title": title,
                            "views": page_views
                        })
        
        # Extract top countries data
        top_countries = []
        total_country_users = 0
        if countries_response.rows:
            # First pass: calculate total users from all countries
            for row in countries_response.rows:
                if row.metric_values:
                    total_country_users += int(row.metric_values[0].value)
            
            # Second pass: create country list with percentages
            for row in countries_response.rows:
                if row.dimension_values and row.metric_values:
                    country = row.dimension_values[0].value
                    country_users = int(row.metric_values[0].value)
                    percentage = round((country_users / total_country_users) * 100, 1) if total_country_users > 0 else 0
                    
                    top_countries.append({
                        "country": country,
                        "users": country_users,
                        "percentage": percentage
                    })
        
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
            "topPages": top_pages,
            "topCountries": top_countries,
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
        print(f"📄 Found {len(top_pages)} popular posts")
        print(f"🌍 Found {len(top_countries)} countries")
        
    except Exception as error:
        print(f"⚠️  Analytics update failed: {error}")
        # Don't fail the build - just skip analytics update
        return False
    
    return True

if __name__ == "__main__":
    success = quick_analytics_update()
    sys.exit(0)  # Always exit successfully to not break the build