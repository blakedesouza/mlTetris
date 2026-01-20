/**
 * ModelManager - Handles model slot operations
 * Provides CRUD operations for saved models and demo mode control
 */
class ModelManager {
    constructor(wsClient) {
        this.wsClient = wsClient;
        this.models = [];
        this.currentDemo = null;  // Currently playing demo slot name
        this.sortColumn = 'name';
        this.sortAsc = true;

        this.setupEventListeners();
        this.loadModels();
    }

    /**
     * Set up event listeners for model management UI
     */
    setupEventListeners() {
        // Save model button
        document.getElementById('btn-save-model').addEventListener('click', () => {
            this.saveCurrentModel();
        });

        // Refresh button
        document.getElementById('btn-refresh-models').addEventListener('click', () => {
            this.loadModels();
        });

        // Table header sorting
        document.querySelectorAll('.model-table th.sortable').forEach(th => {
            th.addEventListener('click', () => {
                const column = th.dataset.sort;
                if (this.sortColumn === column) {
                    this.sortAsc = !this.sortAsc;
                } else {
                    this.sortColumn = column;
                    this.sortAsc = true;
                }
                this.renderTable();
            });
        });
    }

    /**
     * Load models from server
     */
    async loadModels() {
        try {
            const response = await fetch('/api/models');
            if (response.ok) {
                this.models = await response.json();
                this.renderTable();
            } else {
                console.error('Failed to load models:', response.status);
            }
        } catch (error) {
            console.error('Error loading models:', error);
        }
    }

    /**
     * Render model table
     */
    renderTable() {
        const tbody = document.getElementById('model-list');

        if (this.models.length === 0) {
            tbody.innerHTML = '<tr class="empty-row"><td colspan="4">No saved models yet</td></tr>';
            return;
        }

        // Sort models
        const sorted = [...this.models].sort((a, b) => {
            let valA, valB;
            switch (this.sortColumn) {
                case 'name':
                    valA = a.name || '';
                    valB = b.name || '';
                    return this.sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
                case 'lines':
                    valA = a.best_lines || a.config?.target_lines || 0;
                    valB = b.best_lines || b.config?.target_lines || 0;
                    break;
                case 'timesteps':
                    valA = a.total_timesteps_trained || a.num_timesteps || 0;
                    valB = b.total_timesteps_trained || b.num_timesteps || 0;
                    break;
                default:
                    valA = 0;
                    valB = 0;
            }
            return this.sortAsc ? valA - valB : valB - valA;
        });

        // Build table rows
        tbody.innerHTML = sorted.map(model => {
            const name = model.name || 'unknown';
            const lines = model.best_lines || model.config?.target_lines || '-';
            const timesteps = (model.total_timesteps_trained || model.num_timesteps || 0).toLocaleString();
            const isDemo = this.currentDemo === name;

            return `
                <tr data-slot="${name}">
                    <td>${this.escapeHtml(name)}</td>
                    <td>${lines}</td>
                    <td>${timesteps}</td>
                    <td class="action-buttons">
                        <button class="btn-action btn-demo ${isDemo ? 'active' : ''}"
                                onclick="modelManager.toggleDemo('${this.escapeHtml(name)}')"
                                title="${isDemo ? 'Stop Demo' : 'Watch Demo'}">
                            ${isDemo ? 'Stop' : 'Demo'}
                        </button>
                        <button class="btn-action btn-export"
                                onclick="modelManager.exportModel('${this.escapeHtml(name)}')"
                                title="Export model file">
                            Export
                        </button>
                        <button class="btn-action btn-delete"
                                onclick="modelManager.deleteModel('${this.escapeHtml(name)}')"
                                title="Delete model">
                            Delete
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    }

    /**
     * Save current model to a named slot
     */
    async saveCurrentModel() {
        const slotName = prompt('Enter a name for this model slot:', `model_${Date.now()}`);
        if (!slotName) return;

        // Validate slot name (alphanumeric, underscore, hyphen)
        if (!/^[a-zA-Z0-9_-]+$/.test(slotName)) {
            alert('Invalid name. Use only letters, numbers, underscores, and hyphens.');
            return;
        }

        try {
            const response = await fetch('/api/models/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ source: 'best', slot_name: slotName })
            });

            const data = await response.json();
            if (data.success) {
                console.log(`Model saved to slot: ${slotName}`);
                this.loadModels();  // Refresh table
            } else {
                alert(`Failed to save model: ${data.error || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Error saving model:', error);
            alert('Error saving model. Check console for details.');
        }
    }

    /**
     * Delete a model slot
     */
    async deleteModel(slotName) {
        if (!confirm(`Delete model "${slotName}"? This cannot be undone.`)) {
            return;
        }

        try {
            const response = await fetch(`/api/models/${encodeURIComponent(slotName)}`, {
                method: 'DELETE'
            });

            const data = await response.json();
            if (data.success) {
                console.log(`Model deleted: ${slotName}`);
                // Stop demo if deleting current demo model
                if (this.currentDemo === slotName) {
                    this.stopDemo();
                }
                this.loadModels();  // Refresh table
            } else {
                alert(`Failed to delete model: ${data.error || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Error deleting model:', error);
            alert('Error deleting model. Check console for details.');
        }
    }

    /**
     * Export model to downloadable file
     */
    async exportModel(slotName) {
        const filename = `${slotName}.zip`;

        try {
            const response = await fetch('/api/models/export', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ slot_name: slotName, filename: filename })
            });

            const data = await response.json();
            if (data.success) {
                // Create download link
                // Note: The file is saved server-side to exports/
                // For actual download, would need a download endpoint
                alert(`Model exported to: ${data.path}\n\nFile saved on server. Manual retrieval required.`);
            } else {
                alert(`Failed to export model: ${data.error || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Error exporting model:', error);
            alert('Error exporting model. Check console for details.');
        }
    }

    /**
     * Toggle demo mode for a model
     */
    toggleDemo(slotName) {
        if (this.currentDemo === slotName) {
            this.stopDemo();
        } else {
            this.startDemo(slotName);
        }
    }

    /**
     * Start demo mode for a model
     */
    startDemo(slotName) {
        // Stop any existing demo first
        if (this.currentDemo) {
            this.stopDemo();
        }

        // Send via WebSocket
        const sent = this.wsClient.send({
            command: 'demo_start',
            slot_name: slotName
        });

        if (sent) {
            this.currentDemo = slotName;
            this.renderTable();  // Update button state
            console.log(`Demo started: ${slotName}`);
        } else {
            alert('Cannot start demo - not connected to server');
        }
    }

    /**
     * Stop demo mode
     */
    stopDemo() {
        const sent = this.wsClient.send({ command: 'demo_stop' });

        if (sent) {
            this.currentDemo = null;
            this.renderTable();  // Update button state
            console.log('Demo stopped');
        }
    }

    /**
     * Handle status updates from server
     */
    handleStatus(data) {
        if (data.status === 'stopped' && this.currentDemo) {
            this.currentDemo = null;
            this.renderTable();
        } else if (data.status === 'demo_running') {
            // Demo is running - UI should already be updated
        }
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
}

// Global instance - will be created in app.js
let modelManager = null;
