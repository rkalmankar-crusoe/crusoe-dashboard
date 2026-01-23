#!/usr/bin/env python3
"""
Crusoe Cloud Admin API - Datacenter Inventory Fetcher

This script fetches physical datacenter inventory from the admin API.
Provides hierarchical drill-down: Region → Floor → IB Fabric → Rack → GPU

IMPORTANT: Only performs READ operations via admin API.
"""

import json
import requests
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Configuration
ADMIN_API_BASE = "https://admin.crusoecloud.io"
ADMIN_TOKEN_FILE = Path.home() / ".crusoe" / "admin-token-prod"
DATA_DIR = Path(__file__).parent.parent / "data"
INVENTORY_FILE = DATA_DIR / "datacenter_inventory.json"

def get_admin_token():
    """Read admin token from file"""
    try:
        with open(ADMIN_TOKEN_FILE, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"❌ Admin token file not found: {ADMIN_TOKEN_FILE}")
        print("   Please ensure you have admin access configured.")
        return None

def make_admin_request(endpoint, method="GET"):
    """
    Make authenticated request to admin API (READ-only)
    
    Args:
        endpoint (str): API endpoint path
        method (str): HTTP method (default GET for READ-only)
        
    Returns:
        dict or list: Parsed JSON response
    """
    token = get_admin_token()
    if not token:
        return None
        
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    url = f"{ADMIN_API_BASE}{endpoint}"
    
    try:
        print(f"→ GET {endpoint}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"  ❌ HTTP Error {e.response.status_code}: {endpoint}")
        if e.response.status_code == 404:
            print(f"     Endpoint not found. Trying alternative...")
        return None
    except requests.exceptions.Timeout:
        print(f"  ⏱ Timeout fetching {endpoint}")
        return None
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None

def discover_api_endpoints():
    """
    Discover available admin API endpoints (READ-only)
    Try common datacenter inventory endpoints
    """
    print("\n" + "="*60)
    print("DISCOVERING ADMIN API ENDPOINTS (READ-ONLY)")
    print("="*60 + "\n")
    
    # Try common endpoint patterns
    potential_endpoints = [
        "/api/v1/datacenters",
        "/api/v1/inventory",
        "/api/v1/inventory/datacenters",
        "/api/v1/admin/datacenters",
        "/api/v1/admin/inventory",
        "/api/datacenters",
        "/api/inventory",
        "/v1/datacenters",
        "/v1/inventory",
        "/datacenters",
        "/inventory",
    ]
    
    working_endpoints = []
    
    for endpoint in potential_endpoints:
        result = make_admin_request(endpoint)
        if result is not None:
            working_endpoints.append(endpoint)
            print(f"  ✓ Found: {endpoint}")
            print(f"    Response type: {type(result).__name__}")
            if isinstance(result, dict):
                print(f"    Keys: {list(result.keys())[:5]}")
            elif isinstance(result, list):
                print(f"    Count: {len(result)} items")
            print()
    
    if not working_endpoints:
        print("❌ No working endpoints found!")
        print("\nPlease provide the correct admin API endpoint for datacenter inventory.")
    else:
        print(f"\n✓ Found {len(working_endpoints)} working endpoint(s)")
    
    return working_endpoints

def main():
    """Main execution"""
    print("\n" + "="*60)
    print("CRUSOE ADMIN API - DATACENTER INVENTORY FETCHER")
    print("="*60 + "\n")
    
    # Check token availability
    token = get_admin_token()
    if not token:
        print("\n❌ Cannot proceed without admin token")
        return
    
    print(f"✓ Admin token loaded ({len(token)} chars)")
    print(f"✓ API Base: {ADMIN_API_BASE}\n")
    
    # Discover endpoints
    endpoints = discover_api_endpoints()
    
    if not endpoints:
        print("\n📝 Next steps:")
        print("   1. Find the correct admin API endpoint")
        print("   2. Update this script with the endpoint")
        print("   3. Run again to fetch inventory")
    else:
        print("\n✓ Ready to fetch datacenter inventory")
        print("  Update the script to use the correct endpoint from above")

if __name__ == "__main__":
    main()
