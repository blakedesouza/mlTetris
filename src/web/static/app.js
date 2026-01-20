/**
 * ML Tetris Trainer - Main Application
 * Coordinates WebSocket, game board, metrics chart, and UI controls
 */

// Global state
let wsClient = null;
let gameBoard = null;
let metricsChart = null;
let currentStatus = 'stopped';

/**
 * Initialize application when DOM is ready
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('ML Tetris Trainer initializing...');

    // Initialize game board
    gameBoard = new GameBoard('game-board');
    gameBoard.clear();

    // Initialize metrics chart
    metricsChart = new MetricsChart('metrics-chart');

    // Set up UI event handlers
    setupControls();

    // Connect WebSocket
    connectWebSocket();

    console.log('ML Tetris Trainer initialized');
});

/**
 * Connect to WebSocket server
 */
function connectWebSocket() {
    // Determine WebSocket URL (same host, /ws endpoint)
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    wsClient = new WebSocketClient(wsUrl, handleMessage, handleConnectionStatus);
}

/**
 * Handle incoming WebSocket messages
 * @param {object} data - Parsed JSON message
 */
function handleMessage(data) {
    switch (data.type) {
        case 'board':
            // Update game board visualization
            if (data.board) {
                gameBoard.render(data.board);
            }
            break;

        case 'metrics':
            // Update metrics display
            updateMetricsDisplay(data);
            break;

        case 'episode':
            // Episode completed - update chart
            if (data.episode !== undefined) {
                metricsChart.addDataPoint(
                    data.episode,
                    data.reward || 0,
                    data.lines || 0
                );
            }
            break;

        case 'status':
            // Training status changed
            if (data.status) {
                updateTrainingStatus(data.status);
            }
            if (data.message) {
                console.log(`Server: ${data.message}`);
            }
            break;

        case 'info':
            // Informational message
            console.log(`Info: ${data.message}`);
            break;

        case 'error':
            // Error from training
            console.error(`Training error: ${data.error}`);
            if (data.traceback) {
                console.error(data.traceback);
            }
            break;

        default:
            console.log('Unknown message type:', data);
    }
}

/**
 * Handle WebSocket connection status changes
 * @param {string} status - 'connecting', 'connected', 'disconnected', 'failed'
 */
function handleConnectionStatus(status) {
    const indicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');

    switch (status) {
        case 'connecting':
            statusText.textContent = currentStatus + ' (connecting...)';
            break;

        case 'connected':
            statusText.textContent = currentStatus.charAt(0).toUpperCase() + currentStatus.slice(1);
            // Request current status from server
            wsClient.send({ command: 'status' });
            break;

        case 'disconnected':
            statusText.textContent = currentStatus + ' (reconnecting...)';
            break;

        case 'failed':
            statusText.textContent = 'Connection Failed';
            indicator.className = 'status stopped';
            break;
    }
}

/**
 * Update metrics display elements
 * @param {object} data - Metrics data
 */
function updateMetricsDisplay(data) {
    if (data.episode_count !== undefined) {
        document.getElementById('episode-count').textContent = data.episode_count;
    }
    if (data.current_score !== undefined) {
        document.getElementById('current-score').textContent = Math.round(data.current_score);
    }
    if (data.lines_cleared !== undefined) {
        document.getElementById('lines-cleared').textContent = data.lines_cleared;
    }
    if (data.timesteps !== undefined) {
        document.getElementById('timesteps').textContent = data.timesteps.toLocaleString();
    }
    if (data.avg_reward !== undefined) {
        document.getElementById('avg-reward').textContent = data.avg_reward.toFixed(2);
    }
    if (data.best_lines !== undefined) {
        document.getElementById('best-lines').textContent = data.best_lines;
    }
}

/**
 * Update training status indicator and controls
 * @param {string} status - 'stopped', 'running', 'stopping'
 */
function updateTrainingStatus(status) {
    currentStatus = status;

    const indicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');
    const btnStart = document.getElementById('btn-start');
    const btnStop = document.getElementById('btn-stop');
    const configInputs = document.querySelectorAll('.config-item input');

    // Update status indicator
    indicator.className = 'status ' + (status === 'stopping' ? 'paused' : status);
    statusText.textContent = status.charAt(0).toUpperCase() + status.slice(1);

    // Update button states
    btnStart.disabled = (status === 'running' || status === 'stopping');
    btnStop.disabled = (status !== 'running');

    // Disable config inputs while training
    configInputs.forEach(input => {
        input.disabled = (status === 'running' || status === 'stopping');
    });

    // Clear board and chart when stopping
    if (status === 'stopped') {
        // Keep last state visible, don't clear
    }
}

/**
 * Set up UI control event handlers
 */
function setupControls() {
    const btnStart = document.getElementById('btn-start');
    const btnStop = document.getElementById('btn-stop');

    btnStart.addEventListener('click', () => {
        // Get config values from inputs
        const targetLines = parseInt(document.getElementById('target-lines').value) || null;
        const maxTimesteps = parseInt(document.getElementById('max-timesteps').value) || 100000;

        // Send start command with config
        const sent = wsClient.send({
            command: 'start',
            config: {
                target_lines: targetLines,
                max_timesteps: maxTimesteps,
            }
        });

        if (sent) {
            console.log('Start command sent');
            updateTrainingStatus('running');
            metricsChart.clear();  // Clear chart for new training session
        } else {
            console.error('Failed to send start command - not connected');
        }
    });

    btnStop.addEventListener('click', () => {
        const sent = wsClient.send({ command: 'stop' });

        if (sent) {
            console.log('Stop command sent');
            updateTrainingStatus('stopping');
        } else {
            console.error('Failed to send stop command - not connected');
        }
    });
}

// Export for debugging
window.app = {
    gameBoard: () => gameBoard,
    metricsChart: () => metricsChart,
    wsClient: () => wsClient,
    status: () => currentStatus,
};
