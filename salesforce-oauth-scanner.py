#!/usr/bin/env python3
"""
OAuth2 Device Code Flow Vulnerability Checker
Tests multiple Salesforce client IDs for OAuth2 device code flow responses
"""

import requests
import json
import sys
from urllib.parse import urlparse
import time

# List of client IDs to test (from the exploit file)
CLIENT_IDS = [
    "PlatformCLI",
    "SfdcInsights", 
    "SfdcWaveWeb",
    "SfdcMobileChatteriOS",
    "DataLoaderBulkUI/",
    "DataLoaderPartnerUI/"
]

def normalize_salesforce_url(url):
    """
    Normalize Salesforce URL by replacing lightning.force.com with my.salesforce.com
    
    Args:
        url (str): Input URL
        
    Returns:
        str: Normalized URL
    """
    if "lightning.force.com" in url:
        normalized_url = url.replace("lightning.force.com", "my.salesforce.com")
        print(f"🔄 Converting lightning.force.com to my.salesforce.com")
        print(f"   Original: {url}")
        print(f"   Normalized: {normalized_url}")
        print()
        return normalized_url
    return url

def check_oauth2_endpoint(base_url, client_id):
    """
    Test a single OAuth2 endpoint with device code flow
    
    Args:
        base_url (str): Base Salesforce URL
        client_id (str): Client ID to test
        
    Returns:
        dict: Response data if successful, None if failed
    """
    oauth2_url = f"{base_url}/services/oauth2/token"
    
    payload = {
        "scope": "refresh_token api",
        "response_type": "device_code",
        "client_id": client_id
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.post(
            oauth2_url,
            data=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                return response_data
            except json.JSONDecodeError:
                print(f"  ❌ Invalid JSON response for {client_id}")
                return None
        else:
            print(f"  ❌ HTTP {response.status_code} for {client_id}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Request failed for {client_id}: {e}")
        return None

def main():
    """Main function to run the OAuth2 vulnerability check"""
    
    print(" OAuth2 Device Code Flow Vulnerability Checker")
    print("=" * 60)
    
    # Get base URL from user input
    if len(sys.argv) > 1:
        base_url = sys.argv[1].rstrip('/')
    else:
        base_url = input("Enter Salesforce base URL (e.g., https://AAA.my.salesforce.com): ").strip().rstrip('/')
    
    if not base_url:
        print("❌ No URL provided. Exiting.")
        sys.exit(1)
    
    # Normalize URL (replace lightning.force.com with my.salesforce.com)
    base_url = normalize_salesforce_url(base_url)
    
    # Validate URL format
    try:
        parsed_url = urlparse(base_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid URL format")
    except Exception as e:
        print(f"❌ Invalid URL format: {e}")
        sys.exit(1)
    
    print(f"🎯 Testing OAuth2 endpoints on: {base_url}")
    print(f"📋 Testing with {len(CLIENT_IDS)} client IDs...")
    print()
    
    vulnerable_clients = []
    
    for i, client_id in enumerate(CLIENT_IDS, 1):
        print(f"[{i}/{len(CLIENT_IDS)}] Testing ConnectedApp with client_id: {client_id}")
        
        response_data = check_oauth2_endpoint(base_url, client_id)
        
        if response_data and "user_code" in response_data:
            print(f"  ✅ VULNERABLE! Found user_code: {response_data['user_code']}")
            vulnerable_clients.append({
                "client_id": client_id,
                "user_code": response_data["user_code"],
                "device_code": response_data.get("device_code", "N/A"),
                "verification_uri": response_data.get("verification_uri", "N/A"),
                "interval": response_data.get("interval", "N/A")
            })
        elif response_data:
            print(f"  ⚠️  Response received but no user_code found")
            print(f"     Response: {json.dumps(response_data, indent=2)}")
        else:
            print(f"  ❌ No valid response")
        
        print()
        
        # Small delay to avoid overwhelming the server
        time.sleep(0.5)
    
    # Summary
    print("=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    if vulnerable_clients:
        print(f"🚨 VULNERABLE CONNECTED APPS FOUND: {len(vulnerable_clients)}")
        print()
        for client in vulnerable_clients:
            print(f" Client ID: {client['client_id']}")
            print(f"   User Code: {client['user_code']}")
            print(f"   Device Code: {client['device_code']}")
            print(f"   Verification URI: {client['verification_uri']}")
            print(f"   Interval: {client['interval']}")
            print()
    else:
        print("✅ No vulnerable client IDs found")
    
    print(f"Total tested: {len(CLIENT_IDS)}")
    print(f"Vulnerable: {len(vulnerable_clients)}")
    print(f"Secure: {len(CLIENT_IDS) - len(vulnerable_clients)}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Scan interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1) 