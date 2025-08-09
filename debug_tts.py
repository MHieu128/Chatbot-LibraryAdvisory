#!/usr/bin/env python3
"""
Debug TTS trong chat endpoint
"""

import requests
import json

def debug_chat_tts():
    """Debug TTS trong chat response"""
    base_url = "http://localhost:5001"
    
    print("🔍 Debugging TTS in Chat Endpoint\n")
    
    # Test basic response first (no TTS)
    print("1. Testing chat without TTS:")
    response = requests.post(
        f"{base_url}/chat",
        json={"message": "What is Flask?", "enable_tts": False},
        timeout=20
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Response received (no TTS)")
        print(f"   📝 Response length: {len(data.get('response', ''))}")
        print(f"   🔊 Has audio: {data.get('has_audio', False)}")
    else:
        print(f"   ❌ Failed: {response.status_code}")
        
    print()
    
    # Test with TTS enabled
    print("2. Testing chat with TTS enabled:")
    response = requests.post(
        f"{base_url}/chat",
        json={"message": "What is Flask?", "enable_tts": True},
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Response received (with TTS)")
        print(f"   📝 Response length: {len(data.get('response', ''))}")
        print(f"   🔊 Has audio: {data.get('has_audio', False)}")
        
        if data.get('has_audio'):
            print(f"   🎵 Audio URL: {data.get('audio_url')}")
            print(f"   ⏱️  Duration: {data.get('audio_duration', 0):.1f}s")
        else:
            print("   ⚠️  No audio generated!")
            
    else:
        print(f"   ❌ Failed: {response.status_code}")
        try:
            error = response.json()
            print(f"   Error: {error.get('error', 'Unknown')}")
        except:
            print(f"   Raw response: {response.text[:200]}")
    
    print()

    # Test direct TTS with similar text
    print("3. Testing direct TTS generation:")
    
    test_text = "Flask is a lightweight WSGI web application framework written in Python"
    
    response = requests.post(
        f"{base_url}/api/tts/generate",
        json={"text": test_text, "use_cache": False},
        timeout=15
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Direct TTS successful")
        print(f"   📝 Text length: {data.get('text_length')}")
        print(f"   ⏱️  Duration: {data.get('duration_seconds', 0):.1f}s")
        print(f"   🎵 Audio ID: {data.get('audio_id')}")
    else:
        print(f"   ❌ Direct TTS failed: {response.status_code}")
        try:
            error = response.json()
            print(f"   Error: {error.get('error', 'Unknown')}")
        except:
            print(f"   Raw response: {response.text[:200]}")

if __name__ == "__main__":
    debug_chat_tts()
