# Phase 3: Web Visualization - Research

**Researched:** 2026-01-20
**Domain:** Real-time web visualization, Python web servers, WebSocket communication
**Confidence:** HIGH

## Summary

This phase requires building a web dashboard for real-time Tetris AI visualization with training controls. The architecture involves three main components: a Python backend server that manages training and exposes WebSocket endpoints, a frontend that renders the game board on HTML Canvas and displays metrics with Chart.js, and a process management layer that runs training in a separate process to avoid blocking the web server.

The recommended approach uses **FastAPI** for the web server due to its native WebSocket support and superior async performance over Flask-SocketIO. Training runs in a separate **multiprocessing.Process** with **Queue-based communication** to send metrics updates to the web server without blocking. The frontend uses vanilla JavaScript with **HTML Canvas** for game board rendering and **Chart.js** for metrics charts.

**Primary recommendation:** Use FastAPI with native WebSockets, run training in a separate process using multiprocessing.Queue for communication, render the Tetris board by extracting board state and drawing on Canvas (not rgb_array frames).

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | >=0.116.0 | Web server and WebSocket handling | Native async WebSocket support, 3-5x throughput vs Flask |
| uvicorn | >=0.35.0 | ASGI server | Standard for FastAPI, handles async efficiently |
| Jinja2 | >=3.1.0 | HTML templating | Integrated with FastAPI, familiar syntax |
| websockets | >=15.0.0 | WebSocket protocol | Required by FastAPI for WebSocket support |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| aiofiles | >=24.1.0 | Async static file serving | Required for StaticFiles in FastAPI |
| pydantic | >=2.0 | Data validation | Already a FastAPI dependency, use for message schemas |

### Frontend (No additional Python deps)
| Library | Version | Purpose | Delivery |
|---------|---------|---------|----------|
| Chart.js | 4.x | Real-time metrics charts | CDN |
| chartjs-plugin-streaming | 2.x | Streaming data support | CDN (optional, see alternatives) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| FastAPI | Flask-SocketIO | Flask-SocketIO has rooms/namespaces/auto-reconnect built-in, but 40% lower throughput and requires eventlet |
| chartjs-plugin-streaming | Manual Chart.js updates | Plugin is 4 years stale; manual updates with `chart.data.datasets[0].data.push()` is simpler |
| Separate process | Background threads | Python GIL blocks training; process isolation required for CPU-bound work |
| Canvas rendering | rgb_array frames | Board state extraction is more efficient than image encoding/decoding |

**Installation:**
```bash
pip install fastapi uvicorn[standard] jinja2 aiofiles
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── web/                    # Web visualization module
│   ├── __init__.py
│   ├── server.py          # FastAPI app, routes, WebSocket handlers
│   ├── training_manager.py # Process management, Queue communication
│   ├── static/            # CSS, JavaScript files
│   │   ├── styles.css
│   │   ├── app.js         # Main frontend logic
│   │   ├── game-board.js  # Canvas rendering
│   │   └── metrics-chart.js # Chart.js setup
│   └── templates/         # Jinja2 templates
│       └── index.html     # Main dashboard page
├── environment/           # (existing)
└── training/              # (existing)
```

### Pattern 1: Training Process Isolation
**What:** Run SB3 training in a separate Process, communicate via Queues
**When to use:** Always for CPU-bound training to avoid blocking WebSocket server
**Example:**
```python
# Source: Python multiprocessing docs
from multiprocessing import Process, Queue
from typing import Optional

class TrainingManager:
    def __init__(self):
        self.metrics_queue: Queue = Queue()  # Training -> Server
        self.command_queue: Queue = Queue()  # Server -> Training
        self.process: Optional[Process] = None
        self.status: str = "stopped"

    def start_training(self, config: dict):
        if self.process and self.process.is_alive():
            return False
        self.process = Process(
            target=self._training_worker,
            args=(config, self.metrics_queue, self.command_queue)
        )
        self.process.start()
        self.status = "running"
        return True

    def stop_training(self):
        if self.process and self.process.is_alive():
            self.command_queue.put({"command": "stop"})
            self.process.join(timeout=5)
            if self.process.is_alive():
                self.process.terminate()
        self.status = "stopped"

    @staticmethod
    def _training_worker(config, metrics_queue, command_queue):
        # Runs in separate process
        # Create env, agent, train with custom callback that puts metrics on queue
        pass
```

### Pattern 2: WebSocket Connection Manager
**What:** Track active WebSocket connections, broadcast updates to all
**When to use:** For pushing real-time updates to multiple browser tabs
**Example:**
```python
# Source: FastAPI official docs
from fastapi import WebSocket, WebSocketDisconnect
from typing import List

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass  # Handle disconnected clients

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, receive commands
            data = await websocket.receive_json()
            # Handle commands (start/stop training)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

### Pattern 3: Canvas-Based Game Board Rendering
**What:** Draw Tetris board directly from board state array, not rgb_array frames
**When to use:** For efficient web rendering without image encoding overhead
**Example:**
```javascript
// Source: Standard Canvas 2D API
class GameBoard {
    constructor(canvasId, rows = 20, cols = 10) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.rows = rows;
        this.cols = cols;
        this.cellSize = 30;
        this.colors = {
            0: '#1a1a2e',  // Empty
            1: '#00d4ff',  // I
            2: '#ffd700',  // O
            3: '#9400d3',  // T
            4: '#00ff00',  // S
            5: '#ff0000',  // Z
            6: '#0000ff',  // J
            7: '#ff8c00',  // L
        };
    }

    render(boardState) {
        // boardState: 2D array of piece IDs (0 = empty, 1-7 = pieces)
        for (let row = 0; row < this.rows; row++) {
            for (let col = 0; col < this.cols; col++) {
                const cellValue = boardState[row][col];
                this.ctx.fillStyle = this.colors[cellValue] || this.colors[0];
                this.ctx.fillRect(
                    col * this.cellSize,
                    row * this.cellSize,
                    this.cellSize - 1,
                    this.cellSize - 1
                );
            }
        }
    }
}
```

### Pattern 4: Metrics Callback for Queue Communication
**What:** Custom SB3 callback that sends metrics to a Queue
**When to use:** Bridge training process to web server
**Example:**
```python
# Source: SB3 callback pattern + multiprocessing
from stable_baselines3.common.callbacks import BaseCallback
from multiprocessing import Queue

class WebMetricsCallback(BaseCallback):
    def __init__(self, metrics_queue: Queue, update_freq: int = 100):
        super().__init__()
        self.metrics_queue = metrics_queue
        self.update_freq = update_freq
        self.episode_rewards = []
        self.episode_lines = []

    def _on_step(self) -> bool:
        # Check for stop command (non-blocking)
        # Send metrics every update_freq steps
        if self.n_calls % self.update_freq == 0:
            self.metrics_queue.put({
                "type": "metrics",
                "timestep": self.num_timesteps,
                "episode_count": len(self.episode_rewards),
                "mean_reward": sum(self.episode_rewards[-100:]) / max(1, len(self.episode_rewards[-100:])),
            })
        return True  # Continue training
```

### Anti-Patterns to Avoid
- **Training in async handler:** Never run `agent.train()` in an async FastAPI route - blocks event loop
- **Polling for updates:** Don't have frontend poll `/api/status` - use WebSocket push
- **Large message payloads:** Don't send full replay buffer over WebSocket - send only metrics
- **Shared mutable state:** Don't share agent/env objects between processes - use Queues

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| WebSocket protocol | Custom TCP handling | FastAPI native WebSocket | Handles handshake, frames, ping/pong |
| Real-time charts | SVG manipulation | Chart.js | Animation, responsiveness, tooltips |
| Process communication | Socket/file pipes | multiprocessing.Queue | Pickle serialization, thread-safe |
| Static file serving | Manual file reads | FastAPI StaticFiles | Caching, MIME types, security |
| HTML templating | String concatenation | Jinja2 | Escaping, inheritance, filters |
| CORS handling | Manual headers | FastAPI CORSMiddleware | Preflight, credentials, origins |

**Key insight:** The web stack has mature solutions for every component. Focus effort on the training-to-web integration, not reinventing HTTP/WebSocket/charting.

## Common Pitfalls

### Pitfall 1: Blocking the Event Loop
**What goes wrong:** Training runs in async handler, WebSocket connections time out
**Why it happens:** Python GIL + CPU-bound training blocks all async tasks
**How to avoid:** Always run training in separate Process, never in async context
**Warning signs:** WebSocket disconnects during training, unresponsive UI

### Pitfall 2: Queue Memory Buildup
**What goes wrong:** Training produces metrics faster than web server consumes them
**Why it happens:** No backpressure on Queue, unlimited buffering
**How to avoid:** Use non-blocking `queue.get_nowait()`, drop old messages if queue full
**Warning signs:** Growing memory usage, stale metrics displayed

### Pitfall 3: Process Cleanup on Server Restart
**What goes wrong:** Orphaned training processes continue after server stops
**Why it happens:** Process not properly terminated on shutdown
**How to avoid:** Register signal handlers, terminate process in finally/atexit
**Warning signs:** Multiple Python processes in task manager, port already in use

### Pitfall 4: WebSocket Reconnection
**What goes wrong:** Browser tab refresh loses connection, no auto-reconnect
**Why it happens:** Raw WebSocket API doesn't reconnect automatically
**How to avoid:** Implement reconnect logic in frontend JavaScript with exponential backoff
**Warning signs:** "Disconnected" state persists after network blip

### Pitfall 5: CORS Issues in Development
**What goes wrong:** Browser blocks WebSocket or API requests
**Why it happens:** Server not sending proper CORS headers
**How to avoid:** Add CORSMiddleware with appropriate origins early
**Warning signs:** "Access-Control-Allow-Origin" errors in browser console

### Pitfall 6: Board State Extraction
**What goes wrong:** Incorrect board display, wrong piece positions
**Why it happens:** tetris-gymnasium board includes padding/buffer rows
**How to avoid:** Use established pattern: `env.unwrapped.board[0:20, 4:-4]` for playable area
**Warning signs:** Extra empty rows, pieces appearing in wrong columns

## Code Examples

Verified patterns from official sources:

### FastAPI with WebSocket and Static Files
```python
# Source: FastAPI official docs
from fastapi import FastAPI, WebSocket, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

app = FastAPI()
app.mount("/static", StaticFiles(directory="src/web/static"), name="static")
templates = Jinja2Templates(directory="src/web/templates")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            await websocket.send_json({"status": "received", "data": data})
    except WebSocketDisconnect:
        pass
```

### Chart.js Real-Time Update (Manual, No Plugin)
```javascript
// Source: Chart.js docs - simpler than plugin for our use case
const ctx = document.getElementById('metricsChart').getContext('2d');
const chart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            label: 'Episode Reward',
            data: [],
            borderColor: '#00d4ff',
            tension: 0.1
        }]
    },
    options: {
        responsive: true,
        animation: { duration: 0 },  // Disable for performance
        scales: {
            x: { title: { display: true, text: 'Episode' } },
            y: { title: { display: true, text: 'Reward' } }
        }
    }
});

function updateChart(episode, reward) {
    chart.data.labels.push(episode);
    chart.data.datasets[0].data.push(reward);
    // Keep last 100 points for performance
    if (chart.data.labels.length > 100) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
    }
    chart.update('none');  // 'none' skips animation
}
```

### WebSocket Client with Reconnection
```javascript
// Source: Standard WebSocket API + reconnection pattern
class WebSocketClient {
    constructor(url, onMessage) {
        this.url = url;
        this.onMessage = onMessage;
        this.reconnectDelay = 1000;
        this.maxReconnectDelay = 30000;
        this.connect();
    }

    connect() {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
            console.log('Connected');
            this.reconnectDelay = 1000;
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.onMessage(data);
        };

        this.ws.onclose = () => {
            console.log('Disconnected, reconnecting...');
            setTimeout(() => this.connect(), this.reconnectDelay);
            this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxReconnectDelay);
        };
    }

    send(data) {
        if (this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }
}
```

### Async Metrics Polling from Queue
```python
# Source: asyncio + multiprocessing integration pattern
import asyncio
from multiprocessing import Queue

async def poll_metrics(metrics_queue: Queue, manager: ConnectionManager):
    """Background task to poll metrics queue and broadcast to WebSocket clients."""
    while True:
        try:
            # Non-blocking check for new metrics
            while not metrics_queue.empty():
                try:
                    metrics = metrics_queue.get_nowait()
                    await manager.broadcast(metrics)
                except:
                    break
        except Exception as e:
            print(f"Metrics polling error: {e}")
        await asyncio.sleep(0.1)  # 100ms poll interval

# Start on app startup
@app.on_event("startup")
async def start_metrics_polling():
    asyncio.create_task(poll_metrics(training_manager.metrics_queue, connection_manager))
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Flask + eventlet | FastAPI + uvicorn | 2022-2024 | 3-5x WebSocket throughput |
| Socket.IO protocol | Native WebSockets | 2023+ | Simpler, no protocol overhead |
| chartjs-plugin-streaming | Manual Chart.js updates | 2024+ | Plugin unmaintained, manual is simpler |
| rgb_array frame streaming | Board state JSON | Always better | 10x smaller payloads, no encoding |

**Deprecated/outdated:**
- **Flask-SocketIO for new projects:** Still works but FastAPI is now standard for Python async web
- **chartjs-plugin-streaming:** Last updated 2021, Chart.js 4.x compatibility uncertain

## Open Questions

Things that couldn't be fully resolved:

1. **tetris-gymnasium rgb_array support**
   - What we know: Supports "human" and "ansi" render modes confirmed
   - What's unclear: Whether "rgb_array" is implemented (standard Gymnasium pattern suggests yes, but undocumented)
   - Recommendation: Extract board state directly (`env.unwrapped.board`) rather than rely on rgb_array - more efficient anyway

2. **Chart.js 4.x + chartjs-plugin-streaming compatibility**
   - What we know: Plugin 2.x requires Chart.js 3.x
   - What's unclear: Whether plugin 2.x works with Chart.js 4.x
   - Recommendation: Use manual Chart.js updates instead of plugin - simpler, no compatibility concerns

3. **Optimal metrics update frequency**
   - What we know: Too frequent = performance issues, too slow = laggy feel
   - What's unclear: Best balance for this specific use case
   - Recommendation: Start with 100ms (10 updates/sec), adjust based on testing

## Sources

### Primary (HIGH confidence)
- [FastAPI WebSockets Docs](https://fastapi.tiangolo.com/advanced/websockets/) - Server/client patterns
- [FastAPI Templates Docs](https://fastapi.tiangolo.com/advanced/templates/) - Jinja2 integration
- [Python multiprocessing Docs](https://docs.python.org/3/library/multiprocessing.html) - Queue, Process patterns
- [SB3 Callbacks Docs](https://stable-baselines3.readthedocs.io/en/master/guide/callbacks.html) - Custom callback patterns

### Secondary (MEDIUM confidence)
- [TestDriven.io FastAPI WebSocket Tutorial](https://testdriven.io/blog/fastapi-postgres-websockets/) - Real-time dashboard patterns
- [Strapi FastAPI vs Flask](https://strapi.io/blog/fastapi-vs-flask-python-framework-comparison) - Performance comparison
- [Tetris-Gymnasium GitHub](https://github.com/Max-We/Tetris-Gymnasium) - Environment documentation

### Tertiary (LOW confidence)
- [chartjs-plugin-streaming](https://github.com/nagix/chartjs-plugin-streaming) - Streaming plugin (unmaintained, use manual updates instead)
- Various WebSearch results for patterns - verified against primary sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - FastAPI/uvicorn is documented standard, versions verified
- Architecture: HIGH - Patterns from official docs and established practice
- Pitfalls: MEDIUM - Based on documented issues and common patterns
- Board rendering: MEDIUM - Board extraction pattern confirmed from Phase 1, Canvas rendering is standard

**Research date:** 2026-01-20
**Valid until:** 2026-02-20 (30 days - stable domain)
