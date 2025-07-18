#!/usr/bin/env python3
"""
Advanced Proxy Debugging Script
This script will help debug the proxy connection issues more thoroughly.
"""

import requests
import time
from youtube_transcript_api._api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig

def check_ip_address(proxy_username=None, proxy_password=None):
    """Check what IP address we're using"""
    try:
        if proxy_username and proxy_password:
            # Use proxy for IP check
            print("🔄 Checking IP address through proxy...")
            proxies = {
                'http': f'http://{proxy_username}:{proxy_password}@rotating-residential.webshare.io:9000',
                'https': f'http://{proxy_username}:{proxy_password}@rotating-residential.webshare.io:9000'
            }
            response = requests.get('https://httpbin.org/ip', proxies=proxies, timeout=10)
        else:
            print("🔄 Checking direct IP address...")
            response = requests.get('https://httpbin.org/ip', timeout=10)
        
        ip_info = response.json()
        ip_address = ip_info.get('origin', 'Unknown')
        print(f"📍 Current IP: {ip_address}")
        return ip_address
    except Exception as e:
        print(f"❌ Failed to check IP: {str(e)}")
        return None

def test_proxy_configuration():
    """Test if proxy configuration is working at the HTTP level"""
    proxy_username = "sdxliduq"
    proxy_password = "g5cqqf42sd5o"
    
    print("🌐 Testing HTTP Proxy Configuration")
    print("=" * 40)
    
    # Check direct IP
    direct_ip = check_ip_address()
    
    # Check proxy IP
    proxy_ip = check_ip_address(proxy_username, proxy_password)
    
    if direct_ip and proxy_ip and direct_ip != proxy_ip:
        print("✅ Proxy is working - IP addresses are different")
        print(f"   Direct IP: {direct_ip}")
        print(f"   Proxy IP:  {proxy_ip}")
        return True
    elif direct_ip == proxy_ip:
        print("❌ Proxy might not be working - same IP address")
        return False
    else:
        print("⚠️  Could not verify proxy functionality")
        return False

def test_webshare_endpoints():
    """Test different Webshare endpoints"""
    proxy_username = "sdxliduq"
    proxy_password = "g5cqqf42sd5o"
    
    # Different endpoint configurations to try
    endpoints = [
        "rotating-residential.webshare.io:9000",
        "rotating-residential.webshare.io:9001", 
        "rotating-residential.webshare.io:9002",
        "p.webshare.io:80",
        "proxy.webshare.io:80"
    ]
    
    print("🔄 Testing different Webshare endpoints...")
    
    for endpoint in endpoints:
        try:
            print(f"Testing endpoint: {endpoint}")
            proxies = {
                'http': f'http://{proxy_username}:{proxy_password}@{endpoint}',
                'https': f'http://{proxy_username}:{proxy_password}@{endpoint}'
            }
            response = requests.get('https://httpbin.org/ip', proxies=proxies, timeout=5)
            ip_info = response.json()
            print(f"  ✅ {endpoint} works - IP: {ip_info.get('origin')}")
            return endpoint
        except Exception as e:
            print(f"  ❌ {endpoint} failed: {str(e)}")
    
    return None

def test_transcript_with_delays():
    """Test transcript extraction with delays between requests"""
    proxy_username = "sdxliduq"
    proxy_password = "g5cqqf42sd5o"
    
    # Test with a simple, well-known video
    test_video_ids = [
        "dQw4w9WgXcQ",  # Rick Roll - very popular
        "9bZkp7q19f0",  # PSY - Gangnam Style
        "kJQP7kiw5Fk"   # Luis Fonsi - Despacito
    ]
    
    print("🎯 Testing transcript extraction with delays...")
    
    for i, video_id in enumerate(test_video_ids):
        print(f"\nTest {i+1}: Video ID {video_id}")
        print("-" * 30)
        
        try:
            # Use proxy
            ytt_api = YouTubeTranscriptApi(
                proxy_config=WebshareProxyConfig(
                    proxy_username=proxy_username,
                    proxy_password=proxy_password,
                )
            )
            
            print("🔄 Getting transcript list...")
            transcript_list = ytt_api.list_transcripts(video_id)
            print(f"✅ Found {len(list(transcript_list))} transcript(s)")
            
            # Try to get any available transcript
            transcript_list = ytt_api.list_transcripts(video_id)  # Re-get the list
            first_transcript = next(iter(transcript_list))
            print(f"🔄 Fetching {first_transcript.language} transcript...")
            
            transcript_data = first_transcript.fetch()
            print(f"✅ Successfully extracted transcript with {len(transcript_data)} segments!")
            return True
            
        except Exception as e:
            print(f"❌ Failed: {str(e)}")
        
        # Wait between attempts
        if i < len(test_video_ids) - 1:
            print("⏱️  Waiting 5 seconds before next attempt...")
            time.sleep(5)
    
    return False

def main():
    print("🔧 Advanced Proxy Debugging")
    print("=" * 50)
    
    # Test 1: HTTP Proxy functionality
    proxy_working = test_proxy_configuration()
    print()
    
    # Test 2: Different endpoints
    if not proxy_working:
        print("⚠️  Basic proxy test failed, trying different endpoints...")
        working_endpoint = test_webshare_endpoints()
        if working_endpoint:
            print(f"✅ Found working endpoint: {working_endpoint}")
        print()
    
    # Test 3: Transcript extraction with delays
    transcript_success = test_transcript_with_delays()
    
    print("\n🎯 Final Diagnosis:")
    print("=" * 30)
    
    if proxy_working and transcript_success:
        print("✅ Everything is working correctly!")
        print("💡 The original issue might have been temporary or rate limiting")
    elif proxy_working and not transcript_success:
        print("⚠️  Proxy works but transcript extraction fails")
        print("💡 Possible causes:")
        print("   - YouTube is blocking Webshare's IP ranges")
        print("   - Need to wait longer between requests")
        print("   - Try using different Webshare endpoints")
        print("   - Consider switching to datacenter proxies")
    elif not proxy_working:
        print("❌ Proxy configuration issues detected")
        print("💡 Possible causes:")
        print("   - Check your Webshare credentials")
        print("   - Verify your Webshare subscription is active")
        print("   - Try different proxy endpoints")
    
    print("\n💡 Recommendations:")
    print("1. Wait 15-30 minutes between large batches of requests")
    print("2. Add random delays between individual requests (2-5 seconds)")
    print("3. Consider processing smaller batches of videos")
    print("4. Monitor your Webshare usage dashboard")

if __name__ == "__main__":
    main()
