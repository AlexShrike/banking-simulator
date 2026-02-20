/**
 * Banking Simulator Dashboard
 * Real-time dashboard using Preact+HTM for clean, professional UI
 * Handles WebSocket connections and live data updates
 */

// Import Preact and HTM from CDN
import { render, createElement, Component } from 'https://esm.sh/preact@10.19.3';
import { useState, useEffect, useRef } from 'https://esm.sh/preact@10.19.3/hooks';
import { html } from 'https://esm.sh/htm@3.1.1/preact';

// WebSocket connection management
class WebSocketManager {
    constructor(url) {
        this.url = url;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.listeners = new Map();
        this.isConnected = false;
        this.heartbeatInterval = null;
    }

    connect() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.emit('connected', true);
                this.startHeartbeat();
            };

            this.ws.onclose = (event) => {
                console.log('WebSocket disconnected', event.code, event.reason);
                this.isConnected = false;
                this.emit('connected', false);
                this.stopHeartbeat();
                
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    setTimeout(() => this.reconnect(), this.reconnectDelay * Math.pow(2, this.reconnectAttempts));
                }
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.emit('error', error);
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };

        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.emit('error', error);
        }
    }

    reconnect() {
        this.reconnectAttempts++;
        console.log(`Reconnecting... attempt ${this.reconnectAttempts}`);
        this.connect();
    }

    handleMessage(data) {
        const { type } = data;
        this.emit(type, data);
        
        // Handle specific message types
        switch (type) {
            case 'metrics_update':
                this.emit('metrics', data.data);
                break;
            case 'status_update':
                this.emit('status', data.data);
                break;
            case 'transaction_feed':
                this.emit('transaction', data.data);
                break;
            case 'fraud_alert':
                this.emit('fraud_alert', data.data);
                break;
            case 'system_event':
                this.emit('system_event', data);
                break;
            case 'pong':
                // Heartbeat response
                break;
        }
    }

    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        }
    }

    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.isConnected) {
                this.send({ type: 'ping' });
            }
        }, 30000); // Ping every 30 seconds
    }

    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }

    off(event, callback) {
        if (this.listeners.has(event)) {
            const callbacks = this.listeners.get(event);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }

    emit(event, data) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).forEach(callback => callback(data));
        }
    }
}

// API client for REST endpoints
class APIClient {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
    }

    async request(path, options = {}) {
        try {
            const response = await fetch(`${this.baseURL}/api${path}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers,
                },
                ...options,
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API request failed: ${path}`, error);
            throw error;
        }
    }

    async getStatus() {
        return this.request('/status');
    }

    async getMetrics() {
        return this.request('/metrics');
    }

    async getHealth() {
        return this.request('/health');
    }

    async pauseSimulation() {
        return this.request('/control/pause', { method: 'POST' });
    }

    async resumeSimulation() {
        return this.request('/control/resume', { method: 'POST' });
    }

    async stopSimulation() {
        return this.request('/control/stop', { method: 'POST' });
    }

    async setSpeed(multiplier) {
        return this.request('/control/speed', {
            method: 'POST',
            body: JSON.stringify({ multiplier }),
        });
    }
}

// Utility functions
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toLocaleString();
}

function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
        return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
        return `${minutes}m ${secs}s`;
    } else {
        return `${secs}s`;
    }
}

// Main Dashboard Component
function Dashboard() {
    const [connected, setConnected] = useState(false);
    const [simulationStatus, setSimulationStatus] = useState({});
    const [metrics, setMetrics] = useState({});
    const [transactions, setTransactions] = useState([]);
    const [loading, setLoading] = useState({});
    const [error, setError] = useState(null);
    
    const wsManager = useRef(null);
    const apiClient = useRef(new APIClient());

    useEffect(() => {
        // Initialize WebSocket connection
        wsManager.current = new WebSocketManager();
        
        // Set up event listeners
        wsManager.current.on('connected', setConnected);
        wsManager.current.on('status', setSimulationStatus);
        wsManager.current.on('metrics', setMetrics);
        wsManager.current.on('transaction', handleNewTransaction);
        wsManager.current.on('fraud_alert', handleFraudAlert);
        wsManager.current.on('system_event', handleSystemEvent);
        wsManager.current.on('error', handleWebSocketError);

        // Connect
        wsManager.current.connect();

        // Initial data fetch
        loadInitialData();

        // Cleanup on unmount
        return () => {
            wsManager.current.ws?.close();
        };
    }, []);

    const loadInitialData = async () => {
        try {
            const [statusResponse, metricsResponse] = await Promise.all([
                apiClient.current.getStatus().catch(() => ({ data: {} })),
                apiClient.current.getMetrics().catch(() => ({ data: {} }))
            ]);

            setSimulationStatus(statusResponse.data || {});
            setMetrics(metricsResponse.data || {});
        } catch (error) {
            console.error('Failed to load initial data:', error);
            setError('Failed to load initial data');
        }
    };

    const handleNewTransaction = (transaction) => {
        setTransactions(prev => {
            const newTransactions = [transaction, ...prev].slice(0, 50); // Keep last 50
            return newTransactions;
        });
    };

    const handleFraudAlert = (alert) => {
        // Handle fraud alerts
        console.log('Fraud alert:', alert);
        // Could show notification or highlight in UI
    };

    const handleSystemEvent = (event) => {
        console.log('System event:', event);
        // Handle system events like pause/resume
    };

    const handleWebSocketError = (error) => {
        setError(`Connection error: ${error.message || 'Unknown error'}`);
    };

    const handleControlAction = async (action, params = {}) => {
        setLoading(prev => ({ ...prev, [action]: true }));
        setError(null);

        try {
            switch (action) {
                case 'pause':
                    await apiClient.current.pauseSimulation();
                    break;
                case 'resume':
                    await apiClient.current.resumeSimulation();
                    break;
                case 'stop':
                    await apiClient.current.stopSimulation();
                    break;
                case 'setSpeed':
                    await apiClient.current.setSpeed(params.multiplier);
                    break;
            }
        } catch (error) {
            setError(`Failed to ${action}: ${error.message}`);
        } finally {
            setLoading(prev => ({ ...prev, [action]: false }));
        }
    };

    return html`
        <div class="dashboard">
            ${ConnectionStatus({ connected, error })}
            ${ControlPanel({ 
                simulationStatus, 
                onAction: handleControlAction, 
                loading 
            })}
            ${MetricsOverview({ metrics })}
            ${PerformanceMetrics({ metrics })}
            ${TransactionFeed({ transactions })}
        </div>
    `;
}

// Connection Status Component
function ConnectionStatus({ connected, error }) {
    return html`
        <div class="connection-status ${connected ? 'connected' : 'disconnected'}">
            ${connected 
                ? 'Connected to simulation' 
                : error 
                    ? `Disconnected: ${error}`
                    : 'Connecting to simulation...'
            }
        </div>
    `;
}

// Control Panel Component
function ControlPanel({ simulationStatus, onAction, loading }) {
    const [speedInput, setSpeedInput] = useState(100);
    const isRunning = simulationStatus.is_running;
    const isPaused = simulationStatus.is_paused;

    const handleSpeedChange = () => {
        onAction('setSpeed', { multiplier: parseFloat(speedInput) });
    };

    return html`
        <div class="card control-panel">
            <h2>Simulation Control</h2>
            <div class="controls">
                ${!isRunning && html`
                    <button 
                        class="btn btn-primary" 
                        disabled=${loading.start}
                        onclick=${() => onAction('start')}
                    >
                        ${loading.start && html`<span class="loading"></span>`}
                        Start
                    </button>
                `}
                
                ${isRunning && !isPaused && html`
                    <button 
                        class="btn btn-secondary"
                        disabled=${loading.pause}
                        onclick=${() => onAction('pause')}
                    >
                        Pause
                    </button>
                `}
                
                ${isRunning && isPaused && html`
                    <button 
                        class="btn btn-primary"
                        disabled=${loading.resume}
                        onclick=${() => onAction('resume')}
                    >
                        Resume
                    </button>
                `}
                
                ${isRunning && html`
                    <button 
                        class="btn btn-danger"
                        disabled=${loading.stop}
                        onclick=${() => onAction('stop')}
                    >
                        Stop
                    </button>
                `}
                
                <div class="speed-control">
                    <label for="speedInput">Speed:</label>
                    <input 
                        type="number" 
                        class="speed-input"
                        value=${speedInput}
                        min="1" 
                        max="10000" 
                        step="1"
                        oninput=${(e) => setSpeedInput(e.target.value)}
                    />
                    <span>x</span>
                    <button 
                        class="btn btn-primary"
                        disabled=${loading.setSpeed || !isRunning}
                        onclick=${handleSpeedChange}
                    >
                        Set
                    </button>
                </div>
            </div>
        </div>
    `;
}

// Metrics Overview Component
function MetricsOverview({ metrics }) {
    const overview = metrics.overview || {};
    
    return html`
        <div class="card">
            <h2>Overview</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">${formatNumber(overview.transactions_total || 0)}</div>
                    <div class="metric-label">Total Transactions</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${formatNumber(overview.fraud_transactions || 0)}</div>
                    <div class="metric-label">Fraud Detected</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${formatNumber(overview.customers_created || 0)}</div>
                    <div class="metric-label">Customers</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${formatNumber(overview.accounts_created || 0)}</div>
                    <div class="metric-label">Accounts</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${formatDuration(overview.simulation_runtime || 0)}</div>
                    <div class="metric-label">Runtime</div>
                </div>
            </div>
        </div>
    `;
}

// Performance Metrics Component
function PerformanceMetrics({ metrics }) {
    const performance = metrics.performance || {};
    
    return html`
        <div class="card">
            <h2>Performance</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">${(performance.transactions_per_second || 0).toFixed(1)}</div>
                    <div class="metric-label">Transactions/sec</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${Math.round(performance.nexum_latency_p95 || 0)}</div>
                    <div class="metric-label">Nexum Latency (ms)</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${Math.round(performance.bastion_latency_p95 || 0)}</div>
                    <div class="metric-label">Bastion Latency (ms)</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${((performance.nexum_error_rate || 0) * 100).toFixed(1)}%</div>
                    <div class="metric-label">Error Rate</div>
                </div>
            </div>
        </div>
    `;
}

// Transaction Feed Component
function TransactionFeed({ transactions }) {
    if (!transactions.length) {
        return html`
            <div class="card live-feed">
                <h2>Live Transaction Feed</h2>
                <div class="feed-container">
                    <div style="text-align: center; color: #64748b; padding: 2rem;">
                        Waiting for transaction data...
                    </div>
                </div>
            </div>
        `;
    }

    return html`
        <div class="card live-feed">
            <h2>Live Transaction Feed</h2>
            <div class="feed-container">
                ${transactions.map(transaction => html`
                    <div class="transaction-item ${getTransactionClass(transaction)} fade-in" 
                         key=${transaction.transaction_id || Math.random()}>
                        <div>
                            <div>
                                <strong>$${(transaction.amount || 0).toFixed(2)}</strong>
                                ${transaction.description || 'Transaction'}
                            </div>
                            <div class="transaction-meta">
                                ${transaction.channel || 'unknown'} • 
                                Risk: ${(transaction.risk_score || 0).toFixed(3)} •
                                ${new Date(transaction.timestamp || Date.now()).toLocaleTimeString()}
                            </div>
                        </div>
                        <div class="transaction-status">
                            ${getTransactionStatus(transaction)}
                        </div>
                    </div>
                `)}
            </div>
        </div>
    `;
}

function getTransactionClass(transaction) {
    const riskScore = transaction.risk_score || 0;
    const decision = (transaction.decision || 'APPROVE').toUpperCase();
    
    if (decision === 'DECLINE' || riskScore >= 0.8) {
        return 'fraud';
    } else if (decision === 'REVIEW' || riskScore >= 0.5) {
        return 'review';
    }
    return '';
}

function getTransactionStatus(transaction) {
    const decision = (transaction.decision || 'APPROVE').toUpperCase();
    
    switch (decision) {
        case 'DECLINE':
            return '🔴 Declined';
        case 'REVIEW':
            return '🟡 Review';
        case 'APPROVE':
        default:
            return '🟢 Approved';
    }
}

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', () => {
    const container = document.querySelector('.container');
    if (container) {
        render(html`<${Dashboard} />`, container);
    }
});

// Legacy DOM manipulation for backward compatibility
document.addEventListener('DOMContentLoaded', () => {
    updateConnectionStatus();
    setupLegacyEventHandlers();
});

function updateConnectionStatus() {
    const statusElement = document.getElementById('connectionStatus');
    const dotElement = document.getElementById('connectionDot');
    const textElement = document.getElementById('connectionText');
    
    if (statusElement && dotElement && textElement) {
        // This will be updated by the Preact components
        setTimeout(() => {
            statusElement.className = 'connection-status connected';
            statusElement.textContent = 'Connected to simulation';
            dotElement.className = 'status-dot';
            textElement.textContent = 'Connected';
        }, 2000);
    }
}

function setupLegacyEventHandlers() {
    // Setup legacy button handlers for any buttons not handled by Preact
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', (e) => {
            if (!e.defaultPrevented) {
                console.log('Legacy button clicked:', button.id);
            }
        });
    });
}