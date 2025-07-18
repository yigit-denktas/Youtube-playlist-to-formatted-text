#!/usr/bin/env python3
"""
Proxy Test Script for YouTube Transcript API
This script tests if your Webshare proxy credentials are working correctly.
"""

import sys
import time
import random
from youtube_transcript_api._api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled
from youtube_transcript_api.proxies import WebshareProxyConfig

def test_direct_connection(video_id):
    """Test direct connection without proxy"""
    print("🔄 Testing direct connection (no proxy)...")
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list_transcripts(video_id)
        print("✅ Direct connection successful - can access YouTube transcript API")
        return True
    except Exception as e:
        print(f"❌ Direct connection failed: {str(e)}")
        return False

def test_proxy_connection(video_id, proxy_username, proxy_password):
    """Test connection with Webshare proxy"""
    print(f"🔄 Testing proxy connection with username: {proxy_username}")
    try:
        ytt_api = YouTubeTranscriptApi(
            proxy_config=WebshareProxyConfig(
                proxy_username=proxy_username,
                proxy_password=proxy_password,
            )
        )
        transcript_list = ytt_api.list_transcripts(video_id)
        print("✅ Proxy connection successful - can access YouTube transcript API")
        return True
    except Exception as e:
        print(f"❌ Proxy connection failed: {str(e)}")
        return False

def test_transcript_extraction(video_id, proxy_username, proxy_password, use_proxy=True):
    """Test actual transcript extraction"""
    connection_type = "proxy" if use_proxy else "direct"
    print(f"🔄 Testing transcript extraction using {connection_type} connection...")
    
    try:
        if use_proxy:
            ytt_api = YouTubeTranscriptApi(
                proxy_config=WebshareProxyConfig(
                    proxy_username=proxy_username,
                    proxy_password=proxy_password,
                )
            )
        else:
            ytt_api = YouTubeTranscriptApi()
        
        # Get transcript list
        transcript_list = ytt_api.list_transcripts(video_id)
        
        # Try to get English transcript
        try:
            transcript = transcript_list.find_transcript(['en'])
            transcript_data = transcript.fetch()
            print(f"✅ Successfully extracted English transcript ({len(transcript_data)} segments)")
            if transcript_data:
                print(f"📝 First segment: {transcript_data[0].text[:100]}...")
            return True
        except NoTranscriptFound:
            # Try first available transcript
            first_transcript = next(iter(transcript_list))
            print(f"🔄 English not found, trying {first_transcript.language}")
            transcript_data = first_transcript.fetch()
            print(f"✅ Successfully extracted {first_transcript.language} transcript ({len(transcript_data)} segments)")
            if transcript_data:
                print(f"📝 First segment: {transcript_data[0].text[:100]}...")
            return True
            
    except TranscriptsDisabled:
        print("⚠️  Transcripts are disabled for this video")
        return False
    except NoTranscriptFound:
        print("⚠️  No transcripts found for this video")
        return False
    except Exception as e:
        print(f"❌ Transcript extraction failed: {str(e)}")
        return False

def test_multiple_videos(proxy_username, proxy_password):
    """Test with multiple video IDs to see which approach works"""
    # Test videos - popular videos that should have transcripts
    test_videos = [
        ("JAB_plj2rbA", "First test video"),
        ("dQw4w9WgXcQ", "Rick Roll (should have transcripts)"),
        ("9bZkp7q19f0", "Popular video"),
        ("jNQXAC9IVRw", "Another test video")
    ]
    
    print("🎯 Testing multiple videos to find working approach...\n")
    
    for video_id, description in test_videos:
        print(f"Testing: {description} (ID: {video_id})")
        print("-" * 50)
        
        # Test direct first
        direct_success = test_transcript_extraction(video_id, proxy_username, proxy_password, use_proxy=False)
        
        # Test with proxy
        proxy_success = test_transcript_extraction(video_id, proxy_username, proxy_password, use_proxy=True)
        
        print(f"Results for {video_id}:")
        print(f"  Direct: {'✅ Success' if direct_success else '❌ Failed'}")
        print(f"  Proxy:  {'✅ Success' if proxy_success else '❌ Failed'}")
        print()
        
        # If either worked, we found a working video
        if direct_success or proxy_success:
            return video_id, direct_success, proxy_success
            
        # Wait between requests to avoid rate limiting
        time.sleep(2)
    
    return None, False, False

def main():
    print("🚀 YouTube Transcript API Proxy Test")
    print("=" * 50)
    
    # Your proxy credentials
    proxy_username = "sdxliduq"
    proxy_password = "g5cqqf42sd5o"
    
    print(f"Testing with proxy credentials:")
    print(f"Username: {proxy_username}")
    print(f"Password: {'*' * len(proxy_password)}")
    print()
    
    # Test with the same video ID that was failing
    failing_video_id = "JAB_plj2rbA"
    
    print("Phase 1: Connection Tests")
    print("-" * 30)
    
    # Test direct connection
    direct_ok = test_direct_connection(failing_video_id)
    print()
    
    # Test proxy connection
    proxy_ok = test_proxy_connection(failing_video_id, proxy_username, proxy_password)
    print()
    
    print("Phase 2: Transcript Extraction Tests")
    print("-" * 40)
    
    # Test multiple videos
    working_video, direct_worked, proxy_worked = test_multiple_videos(proxy_username, proxy_password)
    
    print("🎯 Final Results:")
    print("=" * 30)
    
    if working_video:
        print(f"✅ Found working video: {working_video}")
        print(f"   Direct connection: {'✅ Works' if direct_worked else '❌ Blocked'}")
        print(f"   Proxy connection:  {'✅ Works' if proxy_worked else '❌ Failed'}")
    else:
        print("❌ All videos failed with both direct and proxy connections")
    
    print("\n🔍 Diagnosis:")
    if not direct_ok and not proxy_ok:
        print("❌ Both direct and proxy connections failed")
        print("💡 Possible issues:")
        print("   - Proxy credentials might be incorrect")
        print("   - Proxy service might be down")
        print("   - YouTube is blocking the proxy IPs as well")
        print("   - Network/firewall issues")
    elif direct_ok and not proxy_ok:
        print("⚠️  Direct connection works but proxy fails")
        print("💡 Possible issues:")
        print("   - Proxy credentials might be incorrect")
        print("   - Proxy configuration issue")
        print("   - Webshare service issue")
    elif not direct_ok and proxy_ok:
        print("✅ Proxy works! Direct connection is blocked")
        print("💡 Your proxy is working correctly")
    else:
        print("✅ Both direct and proxy connections work")
        print("💡 The issue might be request frequency/rate limiting")

if __name__ == "__main__":
    main()
