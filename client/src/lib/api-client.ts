import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
});

// API endpoints
export const api = {
  // Configuration
  getConfig: () => apiClient.get("/config"),

  // Processing
  processYoutubeUrl: (youtubeUrl: string) =>
    apiClient.post("/process_youtube_url", { youtube_url: youtubeUrl }),

  // Status
  getTaskStatus: (taskId: string) => {
    return apiClient.get(`/status/${taskId}`).then((response) => {
      console.log("[API Client] Task status response:", {
        taskId,
        status: response.data.processing_status?.status,
        audioUrl: response.data.audio_file_url,
        fullData: response.data,
      });
      return response;
    });
  },

  // History
  getTaskHistory: (limit = 10, offset = 0) =>
    apiClient.get(`/history?limit=${limit}&offset=${offset}`),

  // Audio
  getAudioFile: (fileName: string) => {
    // Log the input for debugging
    console.log("[API Client] getAudioFile input:", fileName);

    // Handle empty input
    if (!fileName) {
      console.error("[API Client] No fileName provided to getAudioFile");
      return "";
    }

    // If it's already a full URL, return it as is
    if (fileName.startsWith("http")) {
      return fileName;
    }

    // If it's a path containing /api/v1/audio/ already, extract the filename
    if (fileName.includes("/api/v1/audio/")) {
      const parts = fileName.split("/");
      fileName = parts[parts.length - 1];
    } else if (fileName.startsWith("/")) {
      // If it starts with a slash but isn't the full path, get just the filename
      fileName = fileName.split("/").pop() || fileName;
    }

    // Construct the full URL with proper path
    const fullUrl = `${API_BASE_URL}/api/v1/audio/${fileName}`;
    console.log("[API Client] getAudioFile output:", fullUrl);

    return fullUrl;
  },
};
