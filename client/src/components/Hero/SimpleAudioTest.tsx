"use client";

import React, { useRef, useState } from "react";
import { Button } from "@/components/ui/button";

export function SimpleAudioTest() {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [status, setStatus] = useState("");

  const createAndPlayAudio = () => {
    // Get API base URL from environment or use default
    const apiBaseUrl =
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const url = `${apiBaseUrl}/api/v1/audio/test_tone.wav`;

    console.log("Creating audio with URL:", url);
    setStatus("Creating audio...");

    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }

    // First, do a direct fetch to check if the file is accessible
    fetch(url)
      .then((response) => {
        console.log("Fetch test result:", {
          ok: response.ok,
          status: response.status,
          statusText: response.statusText,
          headers: Object.fromEntries(response.headers.entries()),
        });

        if (!response.ok) {
          setStatus(`Fetch failed: ${response.status} ${response.statusText}`);
          return;
        }

        // If fetch succeeds, create and play the audio
        audioRef.current = new Audio();

        audioRef.current.addEventListener("loadstart", () => {
          console.log("Load started");
          setStatus("Loading...");
        });

        audioRef.current.addEventListener("canplay", () => {
          console.log("Can play");
          setStatus("Ready to play");
        });

        audioRef.current.addEventListener("error", (e) => {
          const audio = e.target as HTMLAudioElement;
          let errorMessage = "Unknown error";
          let errorCode = null;

          if (audio.error) {
            errorCode = audio.error.code;
            switch (audio.error.code) {
              case MediaError.MEDIA_ERR_ABORTED:
                errorMessage = "Media download was aborted";
                break;
              case MediaError.MEDIA_ERR_NETWORK:
                errorMessage = "Network error while downloading";
                break;
              case MediaError.MEDIA_ERR_DECODE:
                errorMessage = "Error decoding media";
                break;
              case MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED:
                errorMessage = "Media format not supported";
                break;
            }
          }

          console.error("Audio error details:", {
            errorMessage,
            errorCode,
            networkState: audio.networkState,
            networkStateText: [
              "NETWORK_EMPTY",
              "NETWORK_IDLE",
              "NETWORK_LOADING",
              "NETWORK_NO_SOURCE",
            ][audio.networkState],
            readyState: audio.readyState,
            currentSrc: audio.currentSrc,
            src: audio.src,
          });

          setStatus(`Error: ${errorMessage}`);
        });

        audioRef.current.src = url;
        audioRef.current.load();
      })
      .catch((error) => {
        console.error("Initial fetch failed:", error);
        setStatus(`Fetch error: ${error.message}`);
      });
  };

  const playAudio = () => {
    if (!audioRef.current) {
      setStatus("No audio element");
      return;
    }

    audioRef.current
      .play()
      .then(() => {
        setStatus("Playing");
      })
      .catch((err) => {
        setStatus(`Play error: ${err.message}`);
      });
  };

  return (
    <div className="p-4 border rounded space-y-2">
      <h3 className="font-bold">Simple Audio Test</h3>
      <div className="space-x-2">
        <Button onClick={createAndPlayAudio} size="sm">
          Create Audio
        </Button>
        <Button onClick={playAudio} size="sm">
          Play
        </Button>
      </div>
      <div>Status: {status}</div>
    </div>
  );
}
