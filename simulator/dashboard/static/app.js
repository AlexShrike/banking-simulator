/**
 * Banking Simulator Dashboard - Enhanced Multi-Page Interface
 * Professional dashboard with real-time updates, charts, and comprehensive monitoring
 */

class DashboardApp {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000;
        this.isConnected = false;
        this.isPaused = false;
        this.feedPaused = false;
        
        // Data storage
        this.metrics = {};
        this.status = {};
        this.transactions = [];
        this.customers = [];
        this.scenarios = [];
        this.chartData = {
            tps: [],
            fraud: [],
            latency: [],
            decisions: { approve: 0, review: 0, block: 0 }
        };
        
        // Chart instances
        this.charts = {};
        
        // Initialize the app
        this.init();
    }

    async init() {
        console.log('Initializing Banking Simulator Dashboard');
        
        // Setup navigation
        this.setupNavigation();
        
        // Setup control handlers
        this.setupControlHandlers();
        
        // Setup UI updates
        this.startUIUpdates();
        
        // Load initial data
        await this.loadInitialData();
        
        // Connect WebSocket
        this.connectWebSocket();
        
        // Initialize charts
        this.initializeCharts();
    }

    setupNavigation() {
        const navItems = document.querySelectorAll('.nav-item');
        const pages = document.querySelectorAll('.page');
        const pageTitle = document.getElementById('pageTitle');

        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                
                // Remove active from all nav items
                navItems.forEach(nav => nav.classList.remove('active'));
                
                // Hide all pages
                pages.forEach(page => page.classList.remove('active'));
                
                // Activate clicked item and corresponding page
                item.classList.add('active');
                const targetPage = item.dataset.page;
                const targetPageElement = document.getElementById(targetPage);
                
                if (targetPageElement) {
                    targetPageElement.classList.add('active');
                    
                    // Update page title
                    const titles = {
                        'control': 'Control Panel',
                        'livefeed': 'Live Feed',
                        'metrics': 'Metrics Dashboard',
                        'customers': 'Customers',
                        'scenario': 'Scenario Info',
                        'results': 'Results'
                    };
                    
                    pageTitle.textContent = titles[targetPage] || 'Dashboard';
                    
                    // Trigger page-specific updates
                    this.onPageChange(targetPage);
                }
            });
        });
    }

    setupControlHandlers() {
        // Scenario selection
        document.getElementById('scenarioSelect').addEventListener('change', (e) => {
            console.log('Scenario changed:', e.target.value);
        });

        // Start simulation
        document.getElementById('startBtn').addEventListener('click', async () => {
            await this.startSimulation();
        });

        // Pause simulation
        document.getElementById('pauseBtn').addEventListener('click', async () => {
            await this.pauseSimulation();
        });

        // Resume simulation
        document.getElementById('resumeBtn').addEventListener('click', async () => {
            await this.resumeSimulation();
        });

        // Stop simulation
        document.getElementById('stopBtn').addEventListener('click', async () => {
            await this.stopSimulation();
        });

        // Speed control
        const speedSlider = document.getElementById('speedSlider');
        const speedValue = document.getElementById('speedValue');
        
        speedSlider.addEventListener('input', (e) => {
            speedValue.textContent = e.target.value + 'x';
        });

        document.getElementById('setSpeedBtn').addEventListener('click', async () => {
            const speed = parseInt(speedSlider.value);
            await this.setSpeed(speed);
        });

        // Feed controls
        document.getElementById('pauseFeedBtn').addEventListener('click', () => {
            this.toggleFeedPause();
        });

        document.getElementById('clearFeedBtn').addEventListener('click', () => {
            this.clearFeed();
        });

        // Feed filter
        document.getElementById('feedFilter').addEventListener('change', (e) => {
            this.filterFeed(e.target.value);
        });
    }

    async loadInitialData() {
        try {
            // Load scenarios
            const scenariosResponse = await fetch('/api/scenarios');
            if (scenariosResponse.ok) {
                const data = await scenariosResponse.json();
                this.scenarios = data.data || [];
                this.updateScenarioDropdown();
            }

            // Load status
            const statusResponse = await fetch('/api/status');
            if (statusResponse.ok) {
                const data = await statusResponse.json();
                this.status = data.data || {};
                this.updateStatus();
            }

            // Load metrics
            const metricsResponse = await fetch('/api/metrics');
            if (metricsResponse.ok) {
                const data = await metricsResponse.json();
                this.metrics = data.data || {};
                this.updateMetrics();
            }

        } catch (error) {
            console.error('Error loading initial data:', error);
        }
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus();
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.isConnected = false;
                this.updateConnectionStatus();
                this.scheduleReconnect();
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.isConnected = false;
                this.updateConnectionStatus();
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };

        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.scheduleReconnect();
        }
    }

    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            setTimeout(() => {
                this.reconnectAttempts++;
                console.log(`Reconnecting... attempt ${this.reconnectAttempts}`);
                this.connectWebSocket();
            }, this.reconnectDelay * this.reconnectAttempts);
        }
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'status_update':
                this.status = { ...this.status, ...data.data };
                this.updateStatus();
                break;
                
            case 'metrics_update':
                this.metrics = { ...this.metrics, ...data.data };
                this.updateMetrics();
                this.updateCharts();
                break;
                
            case 'transaction_update':
                this.handleNewTransaction(data.data);
                break;
                
            case 'system_event':
                this.handleSystemEvent(data);
                break;
                
            default:
                console.log('Unknown WebSocket message type:', data.type);
        }
    }

    updateConnectionStatus() {
        const wsStatus = document.getElementById('wsStatus');
        const wsStatusText = document.getElementById('wsStatusText');
        const overlay = document.getElementById('connectionOverlay');

        if (this.isConnected) {
            wsStatus.className = 'status-dot';
            wsStatusText.textContent = 'Connected';
            overlay.style.display = 'none';
        } else {
            wsStatus.className = 'status-dot disconnected';
            wsStatusText.textContent = 'Disconnected';
            overlay.style.display = 'flex';
        }

        // Update service status indicators (mock for now)
        document.getElementById('nexumStatus').className = 'status-dot';
        document.getElementById('bastionStatus').className = 'status-dot';
        document.getElementById('kafkaStatus').className = 'status-dot warning';
    }

    updateScenarioDropdown() {
        const select = document.getElementById('scenarioSelect');
        select.innerHTML = '';
        
        this.scenarios.forEach(scenario => {
            const option = document.createElement('option');
            option.value = scenario.name || scenario;
            option.textContent = scenario.description || scenario.name || scenario;
            select.appendChild(option);
        });
    }

    updateStatus() {
        // Update simulation status display
        const simStatus = document.getElementById('simStatus');
        const simTime = document.getElementById('simTime');
        const realTime = document.getElementById('realTime');
        const simSpeed = document.getElementById('simSpeed');

        if (simStatus) simStatus.textContent = this.status.state || 'Unknown';
        if (simTime) simTime.textContent = this.status.simulation_time || '--';
        if (realTime) realTime.textContent = new Date().toLocaleTimeString();
        if (simSpeed) simSpeed.textContent = (this.status.speed_multiplier || 1) + 'x';

        // Update control buttons
        const isRunning = this.status.state === 'running' || this.status.is_running;
        const isPaused = this.status.state === 'paused' || this.status.is_paused;

        document.getElementById('startBtn').disabled = isRunning;
        document.getElementById('pauseBtn').disabled = !isRunning || isPaused;
        document.getElementById('resumeBtn').disabled = !isPaused;
        document.getElementById('stopBtn').disabled = !isRunning;
        document.getElementById('setSpeedBtn').disabled = !isRunning;

        if (isPaused) {
            document.getElementById('pauseBtn').style.display = 'none';
            document.getElementById('resumeBtn').style.display = 'inline-flex';
        } else {
            document.getElementById('pauseBtn').style.display = 'inline-flex';
            document.getElementById('resumeBtn').style.display = 'none';
        }
    }

    updateMetrics() {
        // Update quick metrics
        const quickTps = document.getElementById('quickTps');
        const quickTotal = document.getElementById('quickTotal');
        const metricTps = document.getElementById('metricTps');
        const metricTotal = document.getElementById('metricTotal');
        const metricFraud = document.getElementById('metricFraud');
        const metricLatency = document.getElementById('metricLatency');

        const tps = this.metrics.transactions_per_second || 0;
        const total = this.metrics.total_transactions || 0;
        const fraudRate = (this.metrics.fraud_rate || 0) * 100;
        const avgLatency = this.metrics.average_latency || 0;

        if (quickTps) quickTps.textContent = tps.toFixed(1);
        if (quickTotal) quickTotal.textContent = this.formatNumber(total);
        if (metricTps) metricTps.textContent = tps.toFixed(1);
        if (metricTotal) metricTotal.textContent = this.formatNumber(total);
        if (metricFraud) metricFraud.textContent = fraudRate.toFixed(1) + '%';
        if (metricLatency) metricLatency.textContent = Math.round(avgLatency) + 'ms';

        // Store data for charts
        const now = Date.now();
        this.chartData.tps.push({ x: now, y: tps });
        this.chartData.fraud.push({ x: now, y: fraudRate });
        this.chartData.latency.push({ x: now, y: avgLatency });

        // Keep only last 60 data points (5 minutes at 5s intervals)
        ['tps', 'fraud', 'latency'].forEach(key => {
            if (this.chartData[key].length > 60) {
                this.chartData[key] = this.chartData[key].slice(-60);
            }
        });
    }

    handleNewTransaction(transaction) {
        if (this.feedPaused) return;

        this.transactions.unshift(transaction);
        
        // Keep only last 100 transactions
        if (this.transactions.length > 100) {
            this.transactions = this.transactions.slice(0, 100);
        }

        // Update decision counts for pie chart
        const decision = transaction.decision ? transaction.decision.toLowerCase() : 'approve';
        if (this.chartData.decisions[decision] !== undefined) {
            this.chartData.decisions[decision]++;
        }

        this.updateTransactionFeed();
    }

    updateTransactionFeed() {
        const feedContainer = document.getElementById('transactionFeed');
        const filter = document.getElementById('feedFilter').value;
        
        let filteredTransactions = this.transactions;
        if (filter !== 'all') {
            filteredTransactions = this.transactions.filter(t => 
                (t.decision || 'approve').toLowerCase() === filter
            );
        }

        if (filteredTransactions.length === 0) {
            feedContainer.innerHTML = `
                <div style="text-align: center; color: #64748b; padding: 2rem;">
                    ${this.transactions.length === 0 ? 'Waiting for transaction data...' : 'No transactions match the current filter.'}
                </div>
            `;
            return;
        }

        feedContainer.innerHTML = filteredTransactions.map(transaction => `
            <div class="transaction-item ${this.getTransactionClass(transaction)}">
                <div>
                    <div>
                        <strong>$${(transaction.amount || 0).toFixed(2)}</strong>
                        ${transaction.description || transaction.type || 'Transaction'}
                        <span class="transaction-meta">
                            ${transaction.customer_name || transaction.customer_id || 'Unknown Customer'}
                        </span>
                    </div>
                    <div class="transaction-meta">
                        ${new Date(transaction.timestamp || Date.now()).toLocaleTimeString()} •
                        Risk: ${(transaction.fraud_score || transaction.risk_score || 0).toFixed(3)} •
                        Latency: ${transaction.latency || 0}ms
                    </div>
                </div>
                <div class="transaction-status">
                    <span class="status-badge ${this.getTransactionClass(transaction)}">
                        ${this.getTransactionStatus(transaction)}
                    </span>
                </div>
            </div>
        `).join('');
    }

    getTransactionClass(transaction) {
        const decision = (transaction.decision || 'approve').toLowerCase();
        const fraudScore = transaction.fraud_score || transaction.risk_score || 0;
        
        if (decision === 'block' || decision === 'decline' || fraudScore >= 0.8) {
            return 'block';
        } else if (decision === 'review' || fraudScore >= 0.5) {
            return 'review';
        }
        return 'approve';
    }

    getTransactionStatus(transaction) {
        const decision = (transaction.decision || 'approve').toLowerCase();
        
        switch (decision) {
            case 'block':
            case 'decline':
                return 'BLOCKED';
            case 'review':
                return 'REVIEW';
            case 'approve':
            default:
                return 'APPROVED';
        }
    }

    initializeCharts() {
        // Initialize simple canvas-based charts
        this.initChart('tpsChart', 'line');
        this.initChart('fraudChart', 'histogram');
        this.initChart('decisionChart', 'pie');
        this.initChart('latencyChart', 'line');
    }

    initChart(containerId, type) {
        const container = document.getElementById(containerId);
        const canvas = container.querySelector('canvas');
        
        if (!canvas) {
            console.warn(`Canvas not found for chart: ${containerId}`);
            return;
        }

        const ctx = canvas.getContext('2d');
        this.charts[containerId] = { canvas, ctx, type };
        
        // Initial empty chart
        this.drawChart(containerId);
    }

    drawChart(chartId) {
        const chart = this.charts[chartId];
        if (!chart) return;

        const { canvas, ctx, type } = chart;
        const width = canvas.width;
        const height = canvas.height;

        // Clear canvas
        ctx.clearRect(0, 0, width, height);
        ctx.fillStyle = '#f8fafc';
        ctx.fillRect(0, 0, width, height);

        // Draw based on chart type
        switch (type) {
            case 'line':
                this.drawLineChart(chartId);
                break;
            case 'histogram':
                this.drawHistogram(chartId);
                break;
            case 'pie':
                this.drawPieChart(chartId);
                break;
        }
    }

    drawLineChart(chartId) {
        const chart = this.charts[chartId];
        const { ctx, canvas } = chart;
        const width = canvas.width;
        const height = canvas.height;

        let data = [];
        if (chartId === 'tpsChart') {
            data = this.chartData.tps;
        } else if (chartId === 'latencyChart') {
            data = this.chartData.latency;
        }

        if (data.length < 2) {
            ctx.fillStyle = '#64748b';
            ctx.font = '14px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('Insufficient data for chart', width / 2, height / 2);
            return;
        }

        // Find min/max for scaling
        const values = data.map(d => d.y);
        const minY = Math.min(...values);
        const maxY = Math.max(...values);
        const range = maxY - minY || 1;

        // Draw axes
        ctx.strokeStyle = '#e2e8f0';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(40, height - 40);
        ctx.lineTo(width - 20, height - 40);
        ctx.moveTo(40, 20);
        ctx.lineTo(40, height - 40);
        ctx.stroke();

        // Draw data line
        if (data.length > 1) {
            ctx.strokeStyle = '#1A3C78';
            ctx.lineWidth = 2;
            ctx.beginPath();

            data.forEach((point, index) => {
                const x = 40 + (index / (data.length - 1)) * (width - 60);
                const y = height - 40 - ((point.y - minY) / range) * (height - 60);

                if (index === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
            });

            ctx.stroke();
        }

        // Draw labels
        ctx.fillStyle = '#64748b';
        ctx.font = '12px sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(maxY.toFixed(1), 35, 25);
        ctx.fillText(minY.toFixed(1), 35, height - 45);
    }

    drawHistogram(chartId) {
        const chart = this.charts[chartId];
        const { ctx, canvas } = chart;
        const width = canvas.width;
        const height = canvas.height;

        // Generate fraud score histogram data
        const bins = 10;
        const binCounts = new Array(bins).fill(0);
        
        this.transactions.forEach(t => {
            const score = t.fraud_score || t.risk_score || 0;
            const binIndex = Math.min(Math.floor(score * bins), bins - 1);
            binCounts[binIndex]++;
        });

        const maxCount = Math.max(...binCounts) || 1;
        const barWidth = (width - 80) / bins;

        // Draw axes
        ctx.strokeStyle = '#e2e8f0';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(40, height - 40);
        ctx.lineTo(width - 20, height - 40);
        ctx.moveTo(40, 20);
        ctx.lineTo(40, height - 40);
        ctx.stroke();

        // Draw bars
        binCounts.forEach((count, index) => {
            const x = 40 + index * barWidth;
            const barHeight = (count / maxCount) * (height - 60);
            const y = height - 40 - barHeight;

            ctx.fillStyle = '#1A3C78';
            ctx.fillRect(x + 1, y, barWidth - 2, barHeight);
        });

        // Labels
        ctx.fillStyle = '#64748b';
        ctx.font = '12px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('Fraud Score Distribution', width / 2, 15);
    }

    drawPieChart(chartId) {
        const chart = this.charts[chartId];
        const { ctx, canvas } = chart;
        const width = canvas.width;
        const height = canvas.height;

        const data = this.chartData.decisions;
        const total = data.approve + data.review + data.block || 1;
        
        const centerX = width / 2;
        const centerY = height / 2;
        const radius = Math.min(width, height) / 3;

        const colors = {
            approve: '#10b981',
            review: '#f59e0b',
            block: '#ef4444'
        };

        let startAngle = 0;

        Object.entries(data).forEach(([key, value]) => {
            const sliceAngle = (value / total) * 2 * Math.PI;
            
            ctx.beginPath();
            ctx.moveTo(centerX, centerY);
            ctx.arc(centerX, centerY, radius, startAngle, startAngle + sliceAngle);
            ctx.closePath();
            ctx.fillStyle = colors[key];
            ctx.fill();
            
            startAngle += sliceAngle;
        });

        // Legend
        ctx.font = '12px sans-serif';
        let legendY = height - 60;
        Object.entries(data).forEach(([key, value]) => {
            ctx.fillStyle = colors[key];
            ctx.fillRect(20, legendY, 12, 12);
            ctx.fillStyle = '#64748b';
            ctx.fillText(`${key}: ${value}`, 40, legendY + 10);
            legendY += 18;
        });
    }

    updateCharts() {
        Object.keys(this.charts).forEach(chartId => {
            this.drawChart(chartId);
        });
    }

    onPageChange(page) {
        switch (page) {
            case 'customers':
                this.loadCustomers();
                break;
            case 'results':
                this.loadResults();
                break;
        }
    }

    async loadCustomers() {
        try {
            const response = await fetch('/api/customers');
            if (response.ok) {
                const data = await response.json();
                this.customers = data.data || [];
                this.updateCustomersList();
            }
        } catch (error) {
            console.error('Error loading customers:', error);
        }
    }

    updateCustomersList() {
        const container = document.getElementById('customersList');
        
        if (this.customers.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; color: #64748b; padding: 2rem;">
                    No customers generated yet...
                </div>
            `;
            return;
        }

        container.innerHTML = this.customers.map(customer => `
            <div class="customer-card">
                <div class="customer-info">
                    <h4>${customer.name || customer.customer_id || 'Unknown Customer'}</h4>
                    <div class="transaction-meta">
                        ${customer.email || ''} • Balance: $${(customer.balance || 0).toFixed(2)}
                    </div>
                    <div class="transaction-meta">
                        Transactions: ${customer.transaction_count || 0}
                    </div>
                </div>
                <div>
                    <span class="risk-badge ${this.getRiskClass(customer.risk_profile)}">
                        ${customer.risk_profile || 'Low'} Risk
                    </span>
                </div>
            </div>
        `).join('');
    }

    getRiskClass(riskProfile) {
        const risk = (riskProfile || 'low').toLowerCase();
        return `risk-${risk}`;
    }

    async loadResults() {
        try {
            const response = await fetch('/api/results');
            if (response.ok) {
                const data = await response.json();
                this.updateResults(data.data || {});
            }
        } catch (error) {
            console.error('Error loading results:', error);
        }
    }

    updateResults(results) {
        const container = document.getElementById('resultsContainer');
        const p50Latency = document.getElementById('p50Latency');
        const p95Latency = document.getElementById('p95Latency');
        const p99Latency = document.getElementById('p99Latency');
        const fraudAccuracy = document.getElementById('fraudAccuracy');
        const falsePositives = document.getElementById('falsePositives');
        const falseNegatives = document.getElementById('falseNegatives');
        const recommendations = document.getElementById('recommendations');

        if (Object.keys(results).length === 0) {
            container.innerHTML = `
                <div style="text-align: center; color: #64748b; padding: 2rem;">
                    No results available yet. Run a simulation to see results.
                </div>
            `;
            return;
        }

        // Update performance metrics
        if (p50Latency) p50Latency.textContent = (results.p50_latency || 0) + 'ms';
        if (p95Latency) p95Latency.textContent = (results.p95_latency || 0) + 'ms';
        if (p99Latency) p99Latency.textContent = (results.p99_latency || 0) + 'ms';

        // Update fraud detection metrics
        if (fraudAccuracy) fraudAccuracy.textContent = ((results.fraud_accuracy || 0) * 100).toFixed(1) + '%';
        if (falsePositives) falsePositives.textContent = results.false_positives || 0;
        if (falseNegatives) falseNegatives.textContent = results.false_negatives || 0;

        // Update recommendations
        if (recommendations && results.recommendations) {
            recommendations.innerHTML = results.recommendations.map(rec => `<p>• ${rec}</p>`).join('');
        }

        // Update summary table
        container.innerHTML = `
            <div class="table-container">
                <table class="table">
                    <tbody>
                        <tr>
                            <td><strong>Total Transactions</strong></td>
                            <td>${this.formatNumber(results.total_transactions || 0)}</td>
                        </tr>
                        <tr>
                            <td><strong>Fraud Detected</strong></td>
                            <td>${results.fraud_detected || 0}</td>
                        </tr>
                        <tr>
                            <td><strong>Average TPS</strong></td>
                            <td>${(results.average_tps || 0).toFixed(2)}</td>
                        </tr>
                        <tr>
                            <td><strong>Peak TPS</strong></td>
                            <td>${(results.peak_tps || 0).toFixed(2)}</td>
                        </tr>
                        <tr>
                            <td><strong>Total Runtime</strong></td>
                            <td>${this.formatDuration(results.runtime_seconds || 0)}</td>
                        </tr>
                        <tr>
                            <td><strong>Error Rate</strong></td>
                            <td>${((results.error_rate || 0) * 100).toFixed(2)}%</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `;
    }

    // Control actions
    async startSimulation() {
        const scenario = document.getElementById('scenarioSelect').value;
        const dryRun = document.getElementById('dryRunToggle').checked;
        
        try {
            const response = await fetch('/api/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ scenario, dry_run: dryRun })
            });
            
            if (response.ok) {
                console.log('Simulation started');
            } else {
                console.error('Failed to start simulation');
            }
        } catch (error) {
            console.error('Error starting simulation:', error);
        }
    }

    async pauseSimulation() {
        try {
            const response = await fetch('/api/control/pause', { method: 'POST' });
            if (response.ok) {
                console.log('Simulation paused');
            }
        } catch (error) {
            console.error('Error pausing simulation:', error);
        }
    }

    async resumeSimulation() {
        try {
            const response = await fetch('/api/control/resume', { method: 'POST' });
            if (response.ok) {
                console.log('Simulation resumed');
            }
        } catch (error) {
            console.error('Error resuming simulation:', error);
        }
    }

    async stopSimulation() {
        try {
            const response = await fetch('/api/control/stop', { method: 'POST' });
            if (response.ok) {
                console.log('Simulation stopped');
            }
        } catch (error) {
            console.error('Error stopping simulation:', error);
        }
    }

    async setSpeed(multiplier) {
        try {
            const response = await fetch('/api/control/speed', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ multiplier })
            });
            
            if (response.ok) {
                console.log(`Speed set to ${multiplier}x`);
            }
        } catch (error) {
            console.error('Error setting speed:', error);
        }
    }

    // Feed controls
    toggleFeedPause() {
        this.feedPaused = !this.feedPaused;
        const btn = document.getElementById('pauseFeedBtn');
        btn.textContent = this.feedPaused ? 'Resume Feed' : 'Pause Feed';
        btn.className = this.feedPaused ? 'btn btn-success' : 'btn btn-secondary';
    }

    clearFeed() {
        this.transactions = [];
        this.updateTransactionFeed();
    }

    filterFeed(filterType) {
        this.updateTransactionFeed();
    }

    // System event handlers
    handleSystemEvent(event) {
        console.log('System event:', event);
        
        switch (event.event_type) {
            case 'simulation_started':
                this.updateStatus();
                break;
            case 'simulation_paused':
                this.updateStatus();
                break;
            case 'simulation_stopped':
                this.updateStatus();
                this.loadResults(); // Load final results
                break;
        }
    }

    // UI updates
    startUIUpdates() {
        // Update real-time clock
        setInterval(() => {
            const realTimeEl = document.getElementById('realTime');
            if (realTimeEl) {
                realTimeEl.textContent = new Date().toLocaleTimeString();
            }
        }, 1000);

        // Update charts periodically
        setInterval(() => {
            if (this.isConnected) {
                this.updateCharts();
            }
        }, 5000);
    }

    // Utility functions
    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toLocaleString();
    }

    formatDuration(seconds) {
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
}

// Initialize the dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new DashboardApp();
});

// Handle page visibility changes to optimize performance
document.addEventListener('visibilitychange', () => {
    if (window.dashboard) {
        if (document.hidden) {
            // Page is hidden, reduce update frequency
            console.log('Dashboard hidden, reducing update frequency');
        } else {
            // Page is visible, resume normal updates
            console.log('Dashboard visible, resuming normal updates');
            if (window.dashboard.isConnected) {
                window.dashboard.updateCharts();
            }
        }
    }
});