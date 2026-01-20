/**
 * WebSocketClient - WebSocket wrapper with auto-reconnection and exponential backoff
 */
class WebSocketClient {
    /**
     * Create WebSocket client
     * @param {string} url - WebSocket URL (e.g., 'ws://localhost:8000/ws')
     * @param {function} onMessage - Callback for received messages
     * @param {function} onStatusChange - Callback for connection status changes
     */
    constructor(url, onMessage, onStatusChange) {
        this.url = url;
        this.onMessage = onMessage;
        this.onStatusChange = onStatusChange || (() => {});

        this.ws = null;
        this.reconnectDelay = 1000;  // Start with 1 second
        this.maxReconnectDelay = 30000;  // Max 30 seconds
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = Infinity;  // Keep trying forever
        this.isIntentionallyClosed = false;

        this.connect();
    }

    /**
     * Establish WebSocket connection
     */
    connect() {
        if (this.isIntentionallyClosed) return;

        console.log(`WebSocket connecting to ${this.url}...`);
        this.onStatusChange('connecting');

        try {
            this.ws = new WebSocket(this.url);
        } catch (e) {
            console.error('WebSocket creation failed:', e);
            this.scheduleReconnect();
            return;
        }

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectDelay = 1000;  // Reset delay on successful connect
            this.reconnectAttempts = 0;
            this.onStatusChange('connected');
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.onMessage(data);
            } catch (e) {
                console.error('Failed to parse WebSocket message:', e);
            }
        };

        this.ws.onclose = (event) => {
            console.log(`WebSocket closed: ${event.code} ${event.reason}`);
            this.onStatusChange('disconnected');

            if (!this.isIntentionallyClosed) {
                this.scheduleReconnect();
            }
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            // onclose will be called after onerror
        };
    }

    /**
     * Schedule reconnection with exponential backoff
     */
    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('Max reconnect attempts reached');
            this.onStatusChange('failed');
            return;
        }

        this.reconnectAttempts++;
        console.log(`Reconnecting in ${this.reconnectDelay}ms (attempt ${this.reconnectAttempts})`);

        setTimeout(() => this.connect(), this.reconnectDelay);

        // Exponential backoff
        this.reconnectDelay = Math.min(
            this.reconnectDelay * 2,
            this.maxReconnectDelay
        );
    }

    /**
     * Send JSON message to server
     * @param {object} data - Data to send
     * @returns {boolean} - True if sent, false if not connected
     */
    send(data) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.warn('WebSocket not connected, cannot send');
            return false;
        }

        try {
            this.ws.send(JSON.stringify(data));
            return true;
        } catch (e) {
            console.error('Failed to send WebSocket message:', e);
            return false;
        }
    }

    /**
     * Close connection intentionally (no reconnect)
     */
    close() {
        this.isIntentionallyClosed = true;
        if (this.ws) {
            this.ws.close();
        }
    }

    /**
     * Check if connected
     * @returns {boolean}
     */
    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }
}
