import { TaskStatusResponse } from '@/types/api-types';

type WebSocketCallback = (data: TaskStatusResponse) => void;

export class WebSocketManager {
  private socket: WebSocket | null = null;
  private callbacks: WebSocketCallback[] = [];
  private taskId: string | null = null;
  private apiBaseUrl: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10; // Increased max attempts
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private pingInterval: NodeJS.Timeout | null = null;
  private pingIntervalMs = 30000; // Send a ping every 30 seconds (increased for Docker stability)

  constructor() {
    this.apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    console.log('[WebSocket] Constructor - API Base URL:', this.apiBaseUrl);
  }

  private getWebSocketUrl(taskId: string): string {
    // If NEXT_PUBLIC_WS_URL is explicitly set, use it
    if (process.env.NEXT_PUBLIC_WS_URL) {
      return `${process.env.NEXT_PUBLIC_WS_URL}/api/v1/ws/status/${taskId}`;
    }

    // Otherwise, derive from API URL
    const wsProtocol = this.apiBaseUrl.startsWith('https') ? 'wss' : 'ws';
    const baseUrl = this.apiBaseUrl.replace(/^https?:\/\//, '');
    return `${wsProtocol}://${baseUrl}/api/v1/ws/status/${taskId}`;
  }

  connect(taskId: string): void {
    console.log(`[WebSocket] Connecting to task: ${taskId}`);

    if (!taskId || taskId === 'null' || taskId === 'undefined') {
      console.error(`[WebSocket] Invalid task ID provided: ${taskId}`);
      return;
    }

    this.disconnect(); // Close any existing connection first
    this.taskId = taskId;
    this.reconnectAttempts = 0;

    // Add delay to ensure task is created on backend before connecting
    setTimeout(() => {
      this.establishConnection();
    }, 1000);
  }

  private async checkBackendHealth(): Promise<boolean> {
    try {
      const healthUrl = `${this.apiBaseUrl}/api/v1/config`;
      console.log(`[WebSocket] Checking backend health at: ${healthUrl}`);

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);

      const response = await fetch(healthUrl, {
        method: 'GET',
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      const isHealthy = response.ok;
      console.log(`[WebSocket] Backend health check: ${isHealthy ? 'HEALTHY' : 'UNHEALTHY'}`);
      return isHealthy;
    } catch (error) {
      console.error('[WebSocket] Backend health check failed:', error);
      return false;
    }
  }

  private async establishConnection(): Promise<void> {
    if (!this.taskId || this.taskId === 'null' || this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log(`[WebSocket] Cannot establish connection - invalid task ID: ${this.taskId}`);
      return;
    }

    // Check if backend is reachable before attempting WebSocket connection
    const isBackendHealthy = await this.checkBackendHealth();
    if (!isBackendHealthy) {
      console.log('[WebSocket] Backend not healthy, delaying connection attempt...');
      setTimeout(() => this.attemptReconnect(), 3000);
      return;
    }

    try {
      const wsUrl = this.getWebSocketUrl(this.taskId);

      console.log(`[WebSocket] Connecting to: ${wsUrl}`);
      console.log(`[WebSocket] API Base URL: ${this.apiBaseUrl}`);
      console.log(`[WebSocket] Task ID: ${this.taskId}`);
      console.log(`[WebSocket] Attempt #${this.reconnectAttempts + 1}/${this.maxReconnectAttempts}`);

      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = () => {
        console.log('[WebSocket] Connection established successfully!');
        this.reconnectAttempts = 0; // Reset on successful connection

        // Setup ping interval after connection is stable (delay for Docker)
        setTimeout(() => {
          this.setupPingInterval();
        }, 2000);
      };

      this.socket.onmessage = (event) => {
        try {
          // Log raw data for debugging
          console.log(`[WebSocket] Received data: ${event.data}`);

          // Handle ping/pong responses (plain text)
          if (event.data === 'pong') {
            console.log('[WebSocket] Received pong response');
            return;
          }

          // Handle other plain text responses
          if (typeof event.data === 'string' && !event.data.startsWith('{')) {
            console.log(`[WebSocket] Received non-JSON message: ${event.data}`);
            return;
          }

          // Parse JSON data
          const data = JSON.parse(event.data) as TaskStatusResponse;
          console.log('[WebSocket] Parsed data:', data);

          this.callbacks.forEach(callback => callback(data));
        } catch (error) {
          console.error('[WebSocket] Error parsing message:', error);
          console.log(`[WebSocket] Raw message that failed parsing: ${event.data}`);
        }
      };

      this.socket.onclose = (event) => {
        console.log(`[WebSocket] Connection closed with code: ${event.code}, reason: ${event.reason}`);

        // Clear ping interval on connection close
        if (this.pingInterval) {
          clearInterval(this.pingInterval);
          this.pingInterval = null;
        }

        // Don't attempt to reconnect with normal closure or if we're intentionally closing
        if (event.code !== 1000 && event.code !== 1001) {
          this.attemptReconnect();
        }
      };

      this.socket.onerror = (event) => {
        console.error('[WebSocket] Connection error occurred. This is often due to network issues or the server being unavailable.');
        console.log(`[WebSocket] Error details - Ready State: ${this.socket?.readyState}, URL: ${wsUrl}`);
        console.log('[WebSocket] This may be due to Docker container not being ready. Will retry...');

        // Don't immediately force close and reconnect - let onclose handle it
        // This prevents aggressive reconnection loops common with Docker timing issues
      };
    } catch (error) {
      console.error('[WebSocket] Error establishing connection:', error);
      this.attemptReconnect();
    }
  }

  private setupPingInterval(): void {
    // Clear existing ping interval if any
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
    }

    // Setup new ping interval
    this.pingInterval = setInterval(() => {
      this.sendPing();
    }, this.pingIntervalMs);
  }

  private attemptReconnect(): void {
    // Clear existing reconnect timeout if any
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      // More conservative backoff for Docker: 2s, 4s, 8s, 16s, etc. with max of 30s
      const delay = Math.min(2000 * Math.pow(2, this.reconnectAttempts - 1), 30000);

      console.log(`[WebSocket] Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms`);

      this.reconnectTimeout = setTimeout(() => {
        console.log(`[WebSocket] Attempting reconnection #${this.reconnectAttempts}`);
        this.establishConnection();
      }, delay);
    } else {
      console.error('[WebSocket] Maximum reconnection attempts reached. Giving up.');
    }
  }

  disconnect(): void {
    console.log('[WebSocket] Disconnecting...');

    // Clear ping interval
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }

    // Clear reconnect timeout
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    // Close socket if it exists
    if (this.socket) {
      console.log('[WebSocket] Closing active socket');

      // Set onclose to null to prevent attempting reconnection when we're intentionally closing
      this.socket.onclose = null;
      this.socket.close();
      this.socket = null;
    }

    this.taskId = null;
    this.callbacks = []; // Clear callbacks
    console.log('[WebSocket] Disconnected');
  }

  subscribe(callback: WebSocketCallback): () => void {
    console.log('[WebSocket] New subscription added');
    this.callbacks.push(callback);
    return () => {
      console.log('[WebSocket] Subscription removed');
      this.callbacks = this.callbacks.filter(cb => cb !== callback);
    };
  }

  sendPing(): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      console.log('[WebSocket] Sending ping');
      this.socket.send('ping');
    } else if (this.socket) {
      console.log(`[WebSocket] Cannot send ping. Socket state: ${this.socket.readyState}`);

      // If the socket is in a closing or closed state, attempt to reconnect
      if (this.socket.readyState === WebSocket.CLOSED || this.socket.readyState === WebSocket.CLOSING) {
        console.log('[WebSocket] Socket closed or closing during ping. Attempting reconnect...');
        this.socket = null; // Clear the socket reference
        this.attemptReconnect();
      }
    } else {
      console.log('[WebSocket] Cannot send ping. No socket exists.');

      // If we should have a socket but don't, attempt to reconnect
      if (this.taskId) {
        this.attemptReconnect();
      }
    }
  }

  // Check if socket is currently connected
  isConnected(): boolean {
    return this.socket !== null && this.socket.readyState === WebSocket.OPEN;
  }
}

export const websocketManager = new WebSocketManager();
