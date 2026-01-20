/**
 * ML Tetris Trainer - Main Application
 * Coordinates WebSocket, game board, and metrics chart
 */

// Initialize components when DOM ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('ML Tetris Trainer initializing...');

    // Initialize game board
    const gameBoard = new GameBoard('game-board');
    gameBoard.clear();

    // Initialize metrics chart
    const metricsChart = new MetricsChart('metrics-chart');

    // Store references globally for debugging
    window.gameBoard = gameBoard;
    window.metricsChart = metricsChart;

    // UI Elements
    const btnStart = document.getElementById('btn-start');
    const btnStop = document.getElementById('btn-stop');
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');

    // Placeholder click handlers (WebSocket integration in Plan 04)
    btnStart.addEventListener('click', () => {
        console.log('Start clicked - WebSocket integration pending');
        // TODO: Send start command via WebSocket
    });

    btnStop.addEventListener('click', () => {
        console.log('Stop clicked - WebSocket integration pending');
        // TODO: Send stop command via WebSocket
    });

    console.log('ML Tetris Trainer ready (WebSocket pending)');
});

/**
 * Update UI elements with metrics data
 * @param {object} data - Metrics data from WebSocket
 */
function updateMetrics(data) {
    if (data.episode_count !== undefined) {
        document.getElementById('episode-count').textContent = data.episode_count;
    }
    if (data.current_score !== undefined) {
        document.getElementById('current-score').textContent = data.current_score;
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
 * Update training status indicator
 * @param {string} status - "stopped", "running", or "paused"
 */
function updateStatus(status) {
    const indicator = document.getElementById('status-indicator');
    const text = document.getElementById('status-text');
    const btnStart = document.getElementById('btn-start');
    const btnStop = document.getElementById('btn-stop');

    indicator.className = 'status ' + status;
    text.textContent = status.charAt(0).toUpperCase() + status.slice(1);

    btnStart.disabled = (status === 'running');
    btnStop.disabled = (status !== 'running');
}
