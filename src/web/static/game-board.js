/**
 * GameBoard - Canvas-based Tetris board renderer
 * Renders board state received from WebSocket as colored cells
 */
class GameBoard {
    constructor(canvasId, rows = 20, cols = 10) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.rows = rows;
        this.cols = cols;
        this.cellSize = this.canvas.width / cols;

        // Tetris piece colors (0 = empty, 1-7 = pieces I, O, T, S, Z, J, L)
        this.colors = {
            0: '#0a0a15',  // Empty
            1: '#00d4ff',  // I - Cyan
            2: '#ffd700',  // O - Yellow
            3: '#9400d3',  // T - Purple
            4: '#00ff00',  // S - Green
            5: '#ff0000',  // Z - Red
            6: '#0000ff',  // J - Blue
            7: '#ff8c00',  // L - Orange
        };
    }

    /**
     * Render board state to canvas
     * @param {number[][]} boardState - 2D array of piece IDs (20 rows x 10 cols)
     */
    render(boardState) {
        // Clear canvas
        this.ctx.fillStyle = this.colors[0];
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        if (!boardState || !boardState.length) return;

        // Draw each cell
        for (let row = 0; row < Math.min(this.rows, boardState.length); row++) {
            for (let col = 0; col < Math.min(this.cols, boardState[row].length); col++) {
                const cellValue = boardState[row][col];
                if (cellValue > 0) {
                    this.drawCell(row, col, cellValue);
                }
            }
        }

        // Draw grid lines
        this.drawGrid();
    }

    /**
     * Draw a single cell with 3D effect
     */
    drawCell(row, col, pieceId) {
        const x = col * this.cellSize;
        const y = row * this.cellSize;
        const size = this.cellSize - 1;
        const color = this.colors[pieceId] || this.colors[1];

        // Main fill
        this.ctx.fillStyle = color;
        this.ctx.fillRect(x, y, size, size);

        // Highlight (top-left)
        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
        this.ctx.fillRect(x, y, size, 3);
        this.ctx.fillRect(x, y, 3, size);

        // Shadow (bottom-right)
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
        this.ctx.fillRect(x, y + size - 3, size, 3);
        this.ctx.fillRect(x + size - 3, y, 3, size);
    }

    /**
     * Draw subtle grid lines
     */
    drawGrid() {
        this.ctx.strokeStyle = 'rgba(0, 212, 255, 0.1)';
        this.ctx.lineWidth = 0.5;

        for (let i = 0; i <= this.cols; i++) {
            this.ctx.beginPath();
            this.ctx.moveTo(i * this.cellSize, 0);
            this.ctx.lineTo(i * this.cellSize, this.canvas.height);
            this.ctx.stroke();
        }

        for (let i = 0; i <= this.rows; i++) {
            this.ctx.beginPath();
            this.ctx.moveTo(0, i * this.cellSize);
            this.ctx.lineTo(this.canvas.width, i * this.cellSize);
            this.ctx.stroke();
        }
    }

    /**
     * Clear the board (show empty state)
     */
    clear() {
        this.ctx.fillStyle = this.colors[0];
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        this.drawGrid();
    }
}
