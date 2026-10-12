#!/usr/bin/env python3
"""
Macfax API Research Tool
Simple script to query Mac pricing and market data
"""

import requests
import json
import sys
from typing import Optional

BASE_URL = "https://macfax.com/api/v1"
API_KEY = None  # Optional: Set your key here or use anonymously

def make_request(endpoint: str, params: dict) -> Optional[dict]:
    """Make API request with optional key"""
    headers = {}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    
    try:
        response = requests.get(f"{BASE_URL}/{endpoint}", params=params, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}", file=sys.stderr)
        return None

def lookup_serial(serial: str):
    """Look up device by serial number"""
    print(f"\n{'='*60}")
    print(f"SERIAL LOOKUP: {serial}")
    print('='*60)
    
    result = make_request("lookup", {"serial": serial})
    if result and result.get("data"):
        data = result["data"]
        print(f"Status: {data.get('status')}")
        print(f"Device: {data.get('device_type')}")
        print(f"Model: {data.get('model')}")
        print(f"Year: {data.get('year')}")
        if data.get('model_identifiers'):
            print(f"Identifiers: {', '.join(data['model_identifiers'])}")
        print(f"\nFull response:\n{json.dumps(data, indent=2)}")

def price_stats(config: str):
    """Get price statistics for a configuration"""
    print(f"\n{'='*60}")
    print(f"PRICE STATS: {config}")
    print('='*60)
    
    result = make_request("price-stats", {"config": config})
    if result and result.get("data"):
        data = result["data"]
        print(f"Configuration: {data.get('config')}")
        print(f"\nSale Estimate: ${data.get('sale_estimate_usd', 'N/A')}")
        print(f"Basis: {data.get('basis', 'N/A')}")
        
        if data.get('asking_band'):
            band = data['asking_band']
            print(f"\nAsking Band:")
            print(f"  Median: ${band.get('median_usd', 'N/A')}")
            print(f"  P25: ${band.get('p25_usd', 'N/A')}")
            print(f"  P75: ${band.get('p75_usd', 'N/A')}")
            print(f"  Sample size: {band.get('sample_size', 'N/A')}")
        
        print(f"\nFull response:\n{json.dumps(data, indent=2)}")

def market_value(model: str):
    """Get market value by model name"""
    print(f"\n{'='*60}")
    print(f"MARKET VALUE: {model}")
    print('='*60)
    
    result = make_request("market", {"model": model})
    if result and result.get("data"):
        data = result["data"]
        print(f"Model: {data.get('model')}")
        
        if data.get('value_usd'):
            print(f"Value: ${data['value_usd']}")
        elif data.get('value_range_usd'):
            range_val = data['value_range_usd']
            print(f"Value Range: ${range_val.get('low')} - ${range_val.get('high')}")
        
        print(f"\nFull response:\n{json.dumps(data, indent=2)}")

def listings(config: str, max_price: Optional[int] = None, sort: str = "price_asc"):
    """Get live listings for a configuration"""
    print(f"\n{'='*60}")
    print(f"LISTINGS: {config}")
    print('='*60)
    
    params = {"config": config, "sort": sort}
    if max_price:
        params["max_price_usd"] = max_price
    
    result = make_request("listings", params)
    if result and result.get("data"):
        listings_data = result["data"].get("listings", [])
        print(f"Found {len(listings_data)} listings\n")
        
        for i, listing in enumerate(listings_data[:10], 1):  # Show first 10
            price = listing.get('ask_usd', listing.get('price_usd', 'N/A'))
            platform = listing.get('platform', 'Unknown')
            title = listing.get('title') or listing.get('headline') or 'No title'
            url = listing.get('url', 'N/A')
            
            print(f"{i}. ${price} - {platform}")
            print(f"   {title}")
            print(f"   {url}\n")
        
        if len(listings_data) > 10:
            print(f"... and {len(listings_data) - 10} more")

def check_listing(url: str):
    """Check trust score for a specific listing"""
    print(f"\n{'='*60}")
    print(f"LISTING CHECK: {url}")
    print('='*60)
    
    result = make_request("check-listing", {"url": url})
    if result and result.get("data"):
        data = result["data"]
        print(f"Known: {data.get('known')}")
        print(f"Live: {data.get('live')}")
        print(f"Flags: {data.get('flags', [])}")
        print(f"\nFull response:\n{json.dumps(data, indent=2)}")


# CLI interface
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Macfax API Research Tool")
        print("\nUsage:")
        print("  python macfax_research.py lookup <serial>")
        print("  python macfax_research.py price <config>")
        print("  python macfax_research.py market <model>")
        print("  python macfax_research.py listings <config> [max_price]")
        print("  python macfax_research.py check <url>")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'lookup' and len(sys.argv) >= 3:
        lookup_serial(sys.argv[2])
    elif command == 'price' and len(sys.argv) >= 3:
        price_stats(sys.argv[2])
    elif command == 'market' and len(sys.argv) >= 3:
        market_value(sys.argv[2])
    elif command == 'listings' and len(sys.argv) >= 3:
        config = sys.argv[2]
        max_price = int(sys.argv[3]) if len(sys.argv) >= 4 else None
        listings(config, max_price)
    elif command == 'check' and len(sys.argv) >= 3:
        check_listing(sys.argv[2])
    else:
        print(f"Invalid command: {command}")
        sys.exit(1)
