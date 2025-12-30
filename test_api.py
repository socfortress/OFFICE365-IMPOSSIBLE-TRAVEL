#!/usr/bin/env python3
"""
Test script to demonstrate the Impossible Travel Detection API

This script simulates login attempts from different locations to test
the impossible travel detection functionality.
"""

import asyncio
import sys
from datetime import datetime, timedelta
from urllib.parse import quote

import httpx


API_BASE_URL = "http://localhost:80"


async def test_analyze(user: str, ip: str, timestamp: str):
    """Test the analyze endpoint"""
    query = f"user={user}|ip={ip}|ts={timestamp}"
    encoded_query = quote(query)
    url = f"{API_BASE_URL}/analyze?query={encoded_query}"

    print(f"\n{'='*80}")
    print(f"Testing: {query}")
    print(f"URL: {url}")
    print(f"{'='*80}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            print(f"\nUser: {data['user']}")
            print(f"IP: {data['current_ip']}")
            print(f"Location: {data['current_location']['city']}, {data['current_location']['country']}")
            print(f"Timestamp: {data['current_timestamp']}")
            print(f"\n🚨 IMPOSSIBLE TRAVEL DETECTED: {data['impossible_travel_detected']}")

            if data.get('previous_login'):
                print(f"\nPrevious Login:")
                print(f"  IP: {data['previous_login']['ip']}")
                print(f"  Location: {data['previous_login']['city']}, {data['previous_login']['country']}")
                print(f"  Timestamp: {data['previous_login']['timestamp']}")

            if data.get('distance_km'):
                print(f"\nTravel Analysis:")
                print(f"  Distance: {data['distance_km']} km")
                print(f"  Time Difference: {data['time_difference_minutes']} minutes")
                print(f"  Calculated Speed: {data['calculated_speed_kmh']} km/h")
                print(f"  Threshold Speed: {data['threshold_speed_kmh']} km/h")

            print(f"\nMessage: {data['message']}")

            return data

    except httpx.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


async def test_purge():
    """Test the purge endpoint"""
    url = f"{API_BASE_URL}/purge"

    print(f"\n{'='*80}")
    print(f"Testing: Purge Database")
    print(f"URL: {url}")
    print(f"{'='*80}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url)
            response.raise_for_status()
            data = response.json()

            print(f"\n✅ Success: {data['success']}")
            print(f"Records Deleted: {data['records_deleted']}")
            print(f"Message: {data['message']}")

            return data

    except httpx.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


async def test_stats():
    """Test the stats endpoint"""
    url = f"{API_BASE_URL}/stats"

    print(f"\n{'='*80}")
    print(f"Testing: Get Statistics")
    print(f"URL: {url}")
    print(f"{'='*80}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            print(f"\n📊 Statistics:")
            print(f"  Total Records: {data['total_records']}")
            print(f"  Unique Users: {data['unique_users']}")

            return data

    except httpx.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


async def run_test_scenario():
    """Run a complete test scenario"""
    print("\n" + "="*80)
    print("🧪 IMPOSSIBLE TRAVEL DETECTION - TEST SCENARIO")
    print("="*80)

    # Test user
    user = "test@example.com"

    # First login from Morocco
    timestamp1 = datetime.now().isoformat()
    await test_analyze(user, "102.78.106.220", timestamp1)
    await asyncio.sleep(2)

    # Second login from USA 5 minutes later (should detect impossible travel)
    timestamp2 = (datetime.now() + timedelta(minutes=5)).isoformat()
    await test_analyze(user, "8.8.8.8", timestamp2)
    await asyncio.sleep(2)

    # Third login from UK 10 minutes later
    timestamp3 = (datetime.now() + timedelta(minutes=10)).isoformat()
    await test_analyze(user, "81.2.69.142", timestamp3)
    await asyncio.sleep(2)

    # Get statistics
    await test_stats()

    # Test purge (optional - comment out if you want to keep data)
    print("\n⚠️  Skipping purge to preserve data. To test purge, uncomment the line below.")
    # await test_purge()

    print("\n" + "="*80)
    print("✅ TEST SCENARIO COMPLETE")
    print("="*80)


async def main():
    """Main function"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "scenario":
            await run_test_scenario()
        elif command == "stats":
            await test_stats()
        elif command == "purge":
            await test_purge()
        elif command == "test":
            if len(sys.argv) < 5:
                print("Usage: python test_api.py test <user> <ip> <timestamp>")
                print("Example: python test_api.py test user@example.com 8.8.8.8 2025-12-10T10:00:00")
                return
            await test_analyze(sys.argv[2], sys.argv[3], sys.argv[4])
        else:
            print(f"Unknown command: {command}")
            print("\nAvailable commands:")
            print("  scenario  - Run a complete test scenario")
            print("  stats     - Get database statistics")
            print("  purge     - Purge the database")
            print("  test      - Test a single login: test <user> <ip> <timestamp>")
    else:
        print("Impossible Travel Detection API - Test Script")
        print("\nUsage: python test_api.py <command>")
        print("\nAvailable commands:")
        print("  scenario  - Run a complete test scenario")
        print("  stats     - Get database statistics")
        print("  purge     - Purge the database")
        print("  test      - Test a single login: test <user> <ip> <timestamp>")
        print("\nExample:")
        print("  python test_api.py scenario")
        print("  python test_api.py test user@example.com 8.8.8.8 2025-12-10T10:00:00")


if __name__ == "__main__":
    asyncio.run(main())
