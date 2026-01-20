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

        case 'demo_metrics':
            // Demo mode metrics - update demo display only
            updateDemoDisplay(data);
            break;

        case 'demo_episode':
            // Demo episode completed - just update display, don't chart
            updateDemoDisplay(data);
            break;

        case 'status':
            // Training status changed
            if (data.status) {
                updateTrainingStatus(data.status);
                // Notify ModelManager of status changes
                if (modelManager) {
                    modelManager.handleStatus(data);
                }
            }
            // Sync control state from server (on reconnect)
            if (data.visual_mode !== undefined) {
                const modeToggle = document.getElementById('mode-toggle');
                modeToggle.checked = data.visual_mode;
                // Update speed slider enabled state
                const speedSlider = document.getElementById('speed-slider');
                speedSlider.disabled = !data.visual_mode || data.status === 'stopped';
            }
            if (data.speed !== undefined) {
                const speedSlider = document.getElementById('speed-slider');
                const speedValue = document.getElementById('speed-value');
                speedSlider.value = data.speed;
                speedValue.textContent = data.speed.toFixed(1) + 'x';
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
            // Error from server - show to user
            console.error(`Server error: ${data.error}`);
            if (data.traceback) {
                console.error(data.traceback);
            }
            // Show error to user
            alert(`Error: ${data.error || data.message || 'Unknown error'}`);
            break;

        case 'ping':
            // Keepalive ping from server - respond with pong
            wsClient.send({ command: 'pong' });
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
            // Initialize ModelManager if not already done
            if (!modelManager && wsClient) {
                modelManager = new ModelManager(wsClient);
            } else if (modelManager) {
                modelManager.loadModels();  // Refresh on reconnect
            }
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
 * @param {string} status - 'stopped', 'running', 'paused', 'stopping'
 */
function updateTrainingStatus(status) {
    currentStatus = status;

    const indicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');
    const btnStart = document.getElementById('btn-start');
    const btnPause = document.getElementById('btn-pause');
    const btnStop = document.getElementById('btn-stop');
    const modeToggle = document.getElementById('mode-toggle');
    const speedSlider = document.getElementById('speed-slider');
    const configInputs = document.querySelectorAll('.config-item input');

    // Update status indicator
    indicator.className = 'status ' + status;
    statusText.textContent = status.charAt(0).toUpperCase() + status.slice(1);

    // Update button states based on status
    switch (status) {
        case 'stopped':
            btnStart.disabled = false;
            btnPause.disabled = true;
            btnPause.textContent = 'Pause';
            btnStop.disabled = true;
            modeToggle.disabled = false;
            speedSlider.disabled = true;  // Only enabled in visual mode while running
            break;

        case 'running':
            btnStart.disabled = true;
            btnPause.disabled = false;
            btnPause.textContent = 'Pause';
            btnStop.disabled = false;
            modeToggle.disabled = false;
            // Speed slider enabled only if visual mode is on
            speedSlider.disabled = !modeToggle.checked;
            break;

        case 'paused':
            btnStart.disabled = true;
            btnPause.disabled = false;
            btnPause.textContent = 'Resume';
            btnStop.disabled = false;
            modeToggle.disabled = false;
            speedSlider.disabled = !modeToggle.checked;
            break;

        case 'stopping':
            btnStart.disabled = true;
            btnPause.disabled = true;
            btnStop.disabled = true;
            modeToggle.disabled = true;
            speedSlider.disabled = true;
            break;

        case 'demo_running':
            btnStart.disabled = true;  // Can't start training during demo
            btnPause.disabled = true;
            btnStop.disabled = false;  // Stop button works for demo too
            modeToggle.disabled = true;  // Mode toggle not applicable in demo
            speedSlider.disabled = false;  // Speed works in demo
            break;
    }

    // Disable config inputs while training or demo
    const isActive = (status === 'running' || status === 'paused' || status === 'stopping' || status === 'demo_running');
    configInputs.forEach(input => {
        input.disabled = isActive;
    });

    // Toggle between training and demo info display
    const trainingInfo = document.getElementById('training-info');
    const demoInfo = document.getElementById('demo-info');
    if (status === 'demo_running') {
        trainingInfo.style.display = 'none';
        demoInfo.style.display = 'flex';
        clearDemoStats();  // Clear stats when demo starts
    } else {
        trainingInfo.style.display = 'flex';
        demoInfo.style.display = 'none';
        if (status === 'stopped') {
            clearDemoStats();  // Clear stats when demo stops
        }
    }
}

/**
 * Update demo mode display
 */
function updateDemoDisplay(data) {
    if (data.episode !== undefined) {
        document.getElementById('demo-episode').textContent = data.episode;
    }
    if (data.score !== undefined) {
        document.getElementById('demo-score').textContent = Math.round(data.score);
    }
    if (data.lines !== undefined) {
        document.getElementById('demo-lines').textContent = data.lines;
    }
}

/**
 * Clear demo stats display
 */
function clearDemoStats() {
    document.getElementById('demo-episode').textContent = '0';
    document.getElementById('demo-score').textContent = '0';
    document.getElementById('demo-lines').textContent = '0';
}

/**
 * Set up UI control event handlers
 */
function setupControls() {
    const btnStart = document.getElementById('btn-start');
    const btnPause = document.getElementById('btn-pause');
    const btnStop = document.getElementById('btn-stop');
    const modeToggle = document.getElementById('mode-toggle');
    const speedSlider = document.getElementById('speed-slider');
    const speedValue = document.getElementById('speed-value');

    // Start button
    btnStart.addEventListener('click', () => {
        // Get config values from inputs
        const targetLines = parseInt(document.getElementById('target-lines').value) || null;
        const trainUntilTarget = document.getElementById('train-until-target').checked;
        // If "train until target" is checked, use very high timesteps (effectively unlimited)
        const maxTimesteps = trainUntilTarget
            ? 999999999
            : (parseInt(document.getElementById('max-timesteps').value) || 100000);

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

            // Sync visual mode and speed if visual is checked
            if (modeToggle.checked) {
                wsClient.send({ command: 'set_mode', visual: true });
                wsClient.send({ command: 'set_speed', speed: parseFloat(speedSlider.value) });
            }
        } else {
            console.error('Failed to send start command - not connected');
        }
    });

    // Pause/Resume button - toggles based on state
    btnPause.addEventListener('click', () => {
        if (currentStatus === 'running') {
            const sent = wsClient.send({ command: 'pause' });
            if (sent) {
                console.log('Pause command sent');
            }
        } else if (currentStatus === 'paused') {
            const sent = wsClient.send({ command: 'resume' });
            if (sent) {
                console.log('Resume command sent');
            }
        }
    });

    // Stop button - works for both training and demo
    btnStop.addEventListener('click', () => {
        // Send stop for training
        const sent = wsClient.send({ command: 'stop' });
        // Also send demo_stop in case it's a demo
        if (modelManager && modelManager.currentDemo) {
            wsClient.send({ command: 'demo_stop' });
        }

        if (sent) {
            console.log('Stop command sent');
            updateTrainingStatus('stopping');
        } else {
            console.error('Failed to send stop command - not connected');
        }
    });

    // Mode toggle - headless vs visual
    modeToggle.addEventListener('change', (e) => {
        const visual = e.target.checked;
        wsClient.send({
            command: 'set_mode',
            visual: visual
        });
        console.log(`Mode set to: ${visual ? 'visual' : 'headless'}`);

        // Enable/disable speed slider based on mode
        speedSlider.disabled = !visual;
    });

    // Speed slider - update display on input
    speedSlider.addEventListener('input', (e) => {
        const speed = parseFloat(e.target.value);
        speedValue.textContent = speed.toFixed(1) + 'x';
    });

    // Speed slider - send command on change (not every input for less WebSocket traffic)
    speedSlider.addEventListener('change', (e) => {
        const speed = parseFloat(e.target.value);
        wsClient.send({
            command: 'set_speed',
            speed: speed
        });
        console.log(`Speed set to: ${speed}`);
    });
}

// Export for debugging
window.app = {
    gameBoard: () => gameBoard,
    metricsChart: () => metricsChart,
    wsClient: () => wsClient,
    status: () => currentStatus,
    modelManager: () => modelManager,
};
