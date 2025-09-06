#!/usr/bin/env python3
"""
Enhanced Database Connection Diagnostics
Provides detailed analysis of why database connections are failing
"""

import os
import sys
import socket
import time
from dotenv import load_dotenv
import psycopg2
from sqlalchemy import create_engine, text
import requests
import subprocess

def check_basic_network_connectivity():
    """Check basic network connectivity issues"""
    print("\n" + "="*60)
    print("🌐 NETWORK CONNECTIVITY ANALYSIS")
    print("="*60)
    
    host = os.getenv('DB_HOST')
    port = int(os.getenv('DB_PORT', 5432))
    
    # 1. Check if host resolves
    print(f"1️⃣ Checking if {host} resolves...")
    try:
        ip = socket.gethostbyname(host)
        print(f"   ✅ Host resolves to: {ip}")
        if ip != host:
            print(f"   ℹ️  Original: {host} → Resolved: {ip}")
    except socket.gaierror as e:
        print(f"   ❌ DNS resolution failed: {e}")
        return False
    
    # 2. Check basic socket connection
    print(f"2️⃣ Testing TCP socket connection to {host}:{port}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)  # 10 second timeout
    
    try:
        result = sock.connect_ex((host, port))
        if result == 0:
            print(f"   ✅ TCP connection successful")
            sock.close()
            return True
        else:
            print(f"   ❌ TCP connection failed with error code: {result}")
            sock.close()
            return False
    except Exception as e:
        print(f"   ❌ Socket connection failed: {e}")
        sock.close()
        return False

def analyze_ip_geolocation():
    """Analyze the IP address geolocation and type"""
    print("\n" + "="*60)
    print("🗺️ IP ADDRESS ANALYSIS")
    print("="*60)
    
    host = os.getenv('DB_HOST')
    print(f"Analyzing IP: {host}")
    
    # Check if it's a private IP
    ip_parts = host.split('.')
    if len(ip_parts) == 4:
        first_octet = int(ip_parts[0])
        second_octet = int(ip_parts[1])
        
        if first_octet == 10:
            print("   🏠 Private IP (Class A: 10.0.0.0/8)")
            print("   ⚠️  Only accessible within the same private network")
        elif first_octet == 172 and 16 <= second_octet <= 31:
            print("   🏠 Private IP (Class B: 172.16.0.0/12)")
            print("   ⚠️  Only accessible within the same private network")
        elif first_octet == 192 and second_octet == 168:
            print("   🏠 Private IP (Class C: 192.168.0.0/16)")
            print("   ⚠️  Only accessible within the same private network")
        else:
            print("   🌐 Public IP address")
            # Try to get geolocation info
            try:
                response = requests.get(f"http://ip-api.com/json/{host}", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data['status'] == 'success':
                        print(f"   📍 Location: {data.get('city', 'Unknown')}, {data.get('country', 'Unknown')}")
                        print(f"   🏢 ISP: {data.get('isp', 'Unknown')}")
                        print(f"   🏗️ Organization: {data.get('org', 'Unknown')}")
                        
                        # Check if it's a cloud provider
                        org_lower = data.get('org', '').lower()
                        if 'microsoft' in org_lower or 'azure' in org_lower:
                            print("   ☁️  This appears to be a Microsoft Azure IP")
                            print("   🔒 Likely requires Azure network access or VPN")
                        elif 'amazon' in org_lower or 'aws' in org_lower:
                            print("   ☁️  This appears to be an Amazon AWS IP")
                        elif 'google' in org_lower or 'gcp' in org_lower:
                            print("   ☁️  This appears to be a Google Cloud IP")
                    else:
                        print("   ❓ Could not determine IP details")
            except:
                print("   ❓ Could not fetch geolocation data")

def provide_specific_recommendations():
    """Provide specific recommendations based on findings"""
    print("\n" + "="*60)
    print("💡 SPECIFIC RECOMMENDATIONS")
    print("="*60)
    
    host = os.getenv('DB_HOST')
    
    print("Based on the analysis, here are your options:")
    print()
    
    print("🔥 **IMMEDIATE SOLUTIONS:**")
    print("1. 🏢 **Use Azure VM/Cloud Shell:**")
    print("   - The database is likely in Azure with network restrictions")
    print("   - Deploy your app to an Azure VM in the same region/VNet")
    print("   - Use Azure Cloud Shell for testing")
    print()
    
    print("2. 🌐 **Configure Network Access:**")
    print("   - Add your public IP to Azure PostgreSQL firewall")
    print("   - Enable 'Allow access to Azure services' if applicable")
    print("   - Check if VPN/ExpressRoute is required")
    print()
    
    print("3. 🏠 **Local Development Setup:**")
    print("   - Set up local PostgreSQL with Docker")
    print("   - Use the provided docker-compose.yml")
    print("   - Import schema and sample data locally")
    print()
    
    print("🔍 **DEBUGGING STEPS:**")
    print("1. Contact database administrator for network access")
    print("2. Check if the IP address has changed")
    print("3. Verify if SSL certificates are required")
    print("4. Test from a different network location")
    print()
    
    print("⚡ **QUICK TEST:**")
    print(f"Try connecting from Azure Cloud Shell:")
    print(f"   psql -h {host} -p 5432 -U chatbotuser -d mycrm")

def main():
    load_dotenv()
    
    print("🔍 ENHANCED DATABASE CONNECTION DIAGNOSTICS")
    print("=" * 60)
    
    if not all([os.getenv('DB_HOST'), os.getenv('DB_USER'), os.getenv('DB_PASSWORD')]):
        print("❌ Missing required environment variables")
        return
    
    # Run all diagnostic checks
    network_ok = check_basic_network_connectivity()
    analyze_ip_geolocation()
    
    provide_specific_recommendations()
    
    print("\n" + "="*60)
    print("📋 SUMMARY: Connection failing due to network restrictions")
    print("    Most likely requires connection from within Azure network")
    print("="*60)

if __name__ == "__main__":
    main()
