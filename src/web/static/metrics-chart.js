/**
 * MetricsChart - Chart.js wrapper for real-time training metrics
 */
class MetricsChart {
    constructor(canvasId) {
        this.ctx = document.getElementById(canvasId).getContext('2d');
        this.maxPoints = 100;  // Keep last 100 data points

        this.chart = new Chart(this.ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Episode Reward',
                        data: [],
                        borderColor: '#00d4ff',
                        backgroundColor: 'rgba(0, 212, 255, 0.1)',
                        tension: 0.1,
                        fill: true,
                    },
                    {
                        label: 'Lines Cleared',
                        data: [],
                        borderColor: '#00ff00',
                        backgroundColor: 'rgba(0, 255, 0, 0.1)',
                        tension: 0.1,
                        fill: true,
                        yAxisID: 'y1',
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 0 },  // Disable for performance
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        labels: { color: '#e8e8e8' }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Episode',
                            color: '#a0a0a0'
                        },
                        ticks: { color: '#a0a0a0' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Reward',
                            color: '#00d4ff'
                        },
                        ticks: { color: '#00d4ff' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Lines',
                            color: '#00ff00'
                        },
                        ticks: { color: '#00ff00' },
                        grid: { drawOnChartArea: false }
                    }
                }
            }
        });
    }

    /**
     * Add new data point to chart
     * @param {number} episode - Episode number
     * @param {number} reward - Episode reward
     * @param {number} lines - Lines cleared in episode
     */
    addDataPoint(episode, reward, lines) {
        this.chart.data.labels.push(episode);
        this.chart.data.datasets[0].data.push(reward);
        this.chart.data.datasets[1].data.push(lines);

        // Remove old points if exceeded max
        if (this.chart.data.labels.length > this.maxPoints) {
            this.chart.data.labels.shift();
            this.chart.data.datasets[0].data.shift();
            this.chart.data.datasets[1].data.shift();
        }

        this.chart.update('none');  // 'none' skips animation
    }

    /**
     * Clear all chart data
     */
    clear() {
        this.chart.data.labels = [];
        this.chart.data.datasets[0].data = [];
        this.chart.data.datasets[1].data = [];
        this.chart.update();
    }
}
