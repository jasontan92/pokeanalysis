"""
Google Cloud Function entry point for the listing monitor.
Triggered by Cloud Scheduler every 30 minutes.
"""

import functions_framework
from monitor import ListingMonitor


@functions_framework.http
def monitor_listings(request):
    """HTTP Cloud Function entry point."""
    try:
        monitor = ListingMonitor()
        new_listings, sold_listings = monitor.run()

        return {
            "status": "success",
            "new_listings": len(new_listings),
            "sold_listings": len(sold_listings)
        }, 200

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }, 500


# For local testing
if __name__ == "__main__":
    result, code = monitor_listings(None)
    print(result)
