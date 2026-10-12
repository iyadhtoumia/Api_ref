#!/usr/bin/env python3
"""
Quick Macfax API Test Script
"""

import requests
import json

BASE_URL = "https://macfax.com/api/v1"

def test_lookup():
    """Test serial lookup"""
    serial = input("Enter serial number (or press Enter for example): ").strip()
    if not serial:
        serial = "C02P73J9G8WP"
    
    print(f"\nLooking up: {serial}...")
    response = requests.get(f"{BASE_URL}/lookup", params={"serial": serial})
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_price_stats():
    """Test price statistics"""
    config = input("Enter config (or press Enter for macbook-pro-14-m3pro-2023): ").strip()
    if not config:
        config = "macbook-pro-14-m3pro-2023"
    
    print(f"\nGetting price stats for: {config}...")
    response = requests.get(f"{BASE_URL}/price-stats", params={"config": config})
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_market():
    """Test market value"""
    model = input("Enter model name (or press Enter for example): ").strip()
    if not model:
        model = "MacBook Air (13-inch, M4, 2025)"
    
    print(f"\nGetting market value for: {model}...")
    response = requests.get(f"{BASE_URL}/market", params={"model": model})
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_listings():
    """Test listings"""
    config = input("Enter config (or press Enter for macbook-pro-14-m3pro-2023): ").strip()
    if not config:
        config = "macbook-pro-14-m3pro-2023"
    
    print(f"\nGetting listings for: {config}...")
    response = requests.get(f"{BASE_URL}/listings", params={"config": config, "sort": "price_asc"})
    print(f"Status: {response.status_code}")
    data = response.json()
    
    if data.get("data", {}).get("listings"):
        print(f"\nFound {len(data['data']['listings'])} listings:")
        for i, listing in enumerate(data['data']['listings'][:5], 1):
            print(f"{i}. {listing}")
    else:
        print(json.dumps(data, indent=2))

def test_get_key():
    """Get a free API key"""
    print("\nRequesting API key...")
    response = requests.post(f"{BASE_URL}/keys")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def main():
    print("Macfax API Test Menu")
    print("=" * 50)
    print("1. Test Serial Lookup")
    print("2. Test Price Statistics")
    print("3. Test Market Value")
    print("4. Test Listings")
    print("5. Get API Key")
    print("6. Run All Tests (with defaults)")
    print("0. Exit")
    
    while True:
        choice = input("\nEnter choice (0-6): ").strip()
        
        if choice == "0":
            print("Goodbye!")
            break
        elif choice == "1":
            test_lookup()
        elif choice == "2":
            test_price_stats()
        elif choice == "3":
            test_market()
        elif choice == "4":
            test_listings()
        elif choice == "5":
            test_get_key()
        elif choice == "6":
            print("\n" + "="*50)
            print("Running all tests with default values...")
            print("="*50)
            test_lookup()
            test_price_stats()
            test_market()
            test_listings()
            break
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    main()
