"use client";

import React, { useState } from 'react';
import { Button } from "@/components/ui/button";

export function TestAudioComponent() {
  const [status, setStatus] = useState('');
  
  const testBackendAudio = async () => {
    const audioUrl = '/api/v1/audio/test_tone.wav';
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const fullUrl = `${apiBaseUrl}${audioUrl}`;
    
    console.log('Testing audio URL:', fullUrl);
    setStatus(`Testing ${fullUrl}...`);
    
    try {
      // First test fetch
      const response = await fetch(fullUrl);
      console.log('Fetch response:', {
        ok: response.ok,
        status: response.status,
        headers: Object.fromEntries(response.headers.entries())
      });
      
      if (!response.ok) {
        setStatus(`Fetch failed: ${response.status} ${response.statusText}`);
        return;
      }
      
      // Try direct audio creation
      const audio = new Audio(fullUrl);
      let eventFired = false;
      
      await new Promise((resolve, reject) => {
        audio.addEventListener('canplaythrough', () => {
          eventFired = true;
          setStatus('Audio loaded successfully!');
          resolve(true);
        });
        
        audio.addEventListener('error', (e) => {
          eventFired = true;
          console.error('Audio error:', e);
          const audioEl = e.target as HTMLAudioElement;
          setStatus(`Audio error: ${audioEl.error?.message || 'Unknown'}`);
          reject(audioEl.error);
        });
        
        // Timeout after 5 seconds
        setTimeout(() => {
          if (!eventFired) {
            setStatus('Timeout waiting for audio to load');
            reject(new Error('Timeout'));
          }
        }, 5000);
      });
      
      // Try to play
      await audio.play();
      setStatus('Audio playing successfully!');
      setTimeout(() => audio.pause(), 1000);
      
    } catch (error) {
      console.error('Test error:', error);
      setStatus(`Error: ${error}`);
    }
  };
  
  return (
    <div className="p-4 border rounded">
      <h3 className="font-bold mb-2">Audio Test Component</h3>
      <Button onClick={testBackendAudio} className="mb-2">
        Test Backend Audio
      </Button>
      <div>Status: {status}</div>
    </div>
  );
}