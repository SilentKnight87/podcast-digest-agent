#!/usr/bin/env python3
"""Test script to verify the dialogue agent fix is working."""

import requests
import time
import json

API_URL = "https://podcast-digest-agent-kzpyml5rvq-uc.a.run.app/api/v1"

def test_pipeline():
    """Test the full pipeline with a known video."""
    # Start processing
    video_id = "dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up
    
    print(f"Starting pipeline for video: {video_id}")
    response = requests.post(
        f"{API_URL}/tasks/process",
        json={"video_ids": [video_id]}
    )
    
    if response.status_code != 200:
        print(f"Error starting process: {response.status_code}")
        print(response.text)
        return
    
    task_id = response.json()["task_id"]
    print(f"Task ID: {task_id}")
    
    # Poll for status
    print("\nPolling for status...")
    for i in range(60):  # Poll for up to 5 minutes
        status_response = requests.get(f"{API_URL}/status/{task_id}")
        if status_response.status_code != 200:
            print(f"Error getting status: {status_response.status_code}")
            break
            
        status_data = status_response.json()
        print(f"Status: {status_data['status']} - {status_data.get('message', '')}")
        
        if status_data["status"] == "completed":
            print("\n✅ Pipeline completed successfully!")
            print(f"Audio path: {status_data.get('result', {}).get('audio_path', 'N/A')}")
            
            # Try to download the audio
            if 'audio_path' in status_data.get('result', {}):
                audio_filename = status_data['result']['audio_path'].split('/')[-1]
                audio_response = requests.get(f"{API_URL}/audio/{audio_filename}")
                if audio_response.status_code == 200:
                    print(f"✅ Audio file accessible: {audio_filename}")
                    print(f"   Size: {len(audio_response.content)} bytes")
                else:
                    print(f"❌ Could not download audio: {audio_response.status_code}")
            break
            
        elif status_data["status"] == "failed":
            print("\n❌ Pipeline failed!")
            print(f"Error: {status_data.get('error', 'Unknown error')}")
            break
            
        time.sleep(5)
    else:
        print("\n⏱️ Timeout waiting for pipeline to complete")

if __name__ == "__main__":
    test_pipeline()