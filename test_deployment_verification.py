#!/usr/bin/env python3
"""Test script to verify the deployment is working correctly."""

import requests
import time
import json

API_URL = "https://podcast-digest-agent-kzpyml5rvq-uc.a.run.app/api/v1"

def test_pipeline():
    """Test the full pipeline with a known video."""
    # Start processing
    video_id = "dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up
    
    print(f"Testing pipeline for video: {video_id}")
    print(f"API URL: {API_URL}")
    
    # Start the process
    response = requests.post(
        f"{API_URL}/tasks/url",
        json={"video_ids": [video_id]},
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\nStart request status: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return
    
    task_data = response.json()
    task_id = task_data.get("task_id")
    print(f"Task ID: {task_id}")
    
    if not task_id:
        print("No task ID returned!")
        return
    
    # Poll for status
    print("\nPolling for status...")
    for i in range(30):  # Poll for up to 2.5 minutes
        status_response = requests.get(f"{API_URL}/tasks/{task_id}")
        if status_response.status_code != 200:
            print(f"Error getting status: {status_response.status_code}")
            print(status_response.text)
            break
            
        status_data = status_response.json()
        status = status_data.get("status", "unknown")
        message = status_data.get("message", "")
        print(f"[{i*5}s] Status: {status} - {message}")
        
        if status == "completed":
            print("\n✅ Pipeline completed successfully!")
            result = status_data.get("result", {})
            audio_path = result.get("audio_path", "N/A")
            print(f"Audio path: {audio_path}")
            
            # Check if it's fallback audio
            if "fallback" in message.lower() or "fallback" in str(result).lower():
                print("❌ WARNING: This appears to be fallback audio!")
            else:
                print("✅ This appears to be actual digest audio!")
                
            # Try to download the audio
            if audio_path and audio_path != "N/A":
                audio_filename = audio_path.split('/')[-1]
                audio_response = requests.get(f"{API_URL}/audio/{audio_filename}")
                if audio_response.status_code == 200:
                    print(f"✅ Audio file accessible: {audio_filename}")
                    print(f"   Size: {len(audio_response.content)} bytes")
                    # Check if it's a reasonable size (not just a tiny fallback)
                    if len(audio_response.content) < 100000:  # Less than 100KB
                        print("❌ WARNING: Audio file is suspiciously small!")
                else:
                    print(f"❌ Could not download audio: {audio_response.status_code}")
            break
            
        elif status == "failed":
            print(f"\n❌ Pipeline failed!")
            print(f"Error: {status_data.get('error', 'Unknown error')}")
            break
            
        time.sleep(5)
    else:
        print("\n⏱️ Timeout waiting for pipeline to complete")

if __name__ == "__main__":
    test_pipeline()