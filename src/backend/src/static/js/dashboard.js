/**
 * Dashboard Management Module
 *
 * Handles credential management, form interactions, and dashboard functionality
 * for the dYdX Trading Service dashboard page.
 */

// Dashboard management class
class DashboardManager {
    constructor() {
        this.authToken = sessionStorage.getItem('auth_token');
        this.userAddress = sessionStorage.getItem('user_address');
        this.currentTab = 'credentials';

        // Equity Curve properties
        this.equityChart = null;
        this.growthChart = null;
        this.currentEquityDays = 30;

        // Initialize if authenticated
        if (this.authToken && this.userAddress) {
            this.initialize();
        } else {
            this.redirectToLogin();
        }
    }

    /**
     * Initialize dashboard
     */
    async initialize() {
        try {
            // Load dashboard data
            await this.loadDashboardData();

            // Load account balance
            await this.loadAccountBalance();

            // Set up event listeners
            this.setupEventListeners();

            // Update user address display
            this.updateUserAddress();

            // Load initial tab content
            this.showTab('credentials');

        } catch (error) {
            console.error('Dashboard initialization error:', error);
            this.showError('Failed to load dashboard. Please refresh the page.');
        }
    }

    /**
     * Load dashboard data from API
     */
    async loadDashboardData() {
        try {
            this.showLoading('Loading dashboard data...');

            const response = await fetch('/api/user/dashboard', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json',
                }
            });

            if (response.status === 401) {
                this.redirectToLogin();
                return;
            }

            const data = await response.json();

            if (response.ok) {
                this.updateDashboardData(data);
            } else {
                this.showError(data.detail || 'Failed to load dashboard data.');
            }

        } catch (error) {
            console.error('Dashboard data load error:', error);
            this.showError('Failed to load dashboard data. Please check your connection.');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * Update dashboard with loaded data
     */
    updateDashboardData(data) {
        // Update status indicators
        this.updateStatusIndicators(data.credentials_status);

        // Update webhook information
        if (data.webhook_info) {
            document.getElementById('webhook-url').value = data.webhook_info.webhook_url || '';
        }

        // Update profile information
        if (data.user_profile) {
            document.getElementById('profile-address').value = data.user_profile.wallet_address || '';
            document.getElementById('profile-created').value = data.user_profile.created_at ?
                new Date(data.user_profile.created_at).toLocaleDateString() : '';
            document.getElementById('account-age').textContent = data.user_profile.account_age_days || '0';
            
            // Auto-populate dYdX wallet address (same as authenticated address)
            document.getElementById('dydx-address').value = data.user_profile.wallet_address || '';
        }

        // Handle mnemonic field - NEVER display the actual mnemonic
        const mnemonicField = document.getElementById('dydx-mnemonic');
        const mnemonicStatus = document.getElementById('mnemonic-status');
        
        if (data.credentials_status.dydx_configured) {
            // Clear the field and show status
            mnemonicField.value = '';
            mnemonicField.placeholder = 'Mnemonic already configured securely (leave blank to keep current)';
            if (mnemonicStatus) {
                mnemonicStatus.classList.remove('hidden');
            }
        } else {
            mnemonicField.placeholder = 'Enter your 12 or 24 word mnemonic phrase';
            if (mnemonicStatus) {
                mnemonicStatus.classList.add('hidden');
            }
        }

        // Handle Telegram credentials - NEVER display after saving
        const telegramTokenField = document.getElementById('telegram-token');
        const telegramChatIdField = document.getElementById('telegram-chat-id');
        const telegramTokenStatus = document.getElementById('telegram-token-status');
        const telegramChatIdStatus = document.getElementById('telegram-chatid-status');
        
        if (data.credentials_status.telegram_configured) {
            // Clear the fields and show status
            telegramTokenField.value = '';
            telegramChatIdField.value = '';
            telegramTokenField.placeholder = 'Token already configured securely (leave blank to keep current)';
            telegramChatIdField.placeholder = 'Chat ID already configured securely (leave blank to keep current)';
            
            if (telegramTokenStatus) {
                telegramTokenStatus.classList.remove('hidden');
            }
            if (telegramChatIdStatus) {
                telegramChatIdStatus.classList.remove('hidden');
            }
        } else {
            telegramTokenField.placeholder = '123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11';
            telegramChatIdField.placeholder = '-1001234567890';
            
            if (telegramTokenStatus) {
                telegramTokenStatus.classList.add('hidden');
            }
            if (telegramChatIdStatus) {
                telegramChatIdStatus.classList.add('hidden');
            }
        }

        // Show security warnings if needed
        this.showSecurityWarnings(data.credentials_status);
    }

    /**
     * Update status indicators based on credentials status
     */
    updateStatusIndicators(credentialsStatus) {
        // dYdX status
        const dydxIndicator = document.getElementById('dydx-indicator');
        const dydxStatusText = document.getElementById('dydx-status-text');
        const dydxBadge = document.getElementById('dydx-badge');

        if (credentialsStatus.dydx_configured) {
            dydxIndicator.classList.remove('bg-red-900');
            dydxIndicator.classList.add('bg-green-900');
            dydxIndicator.innerHTML = `
                <svg class="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
            `;
            dydxStatusText.textContent = 'Configured';
            dydxStatusText.classList.remove('text-red-400');
            dydxStatusText.classList.add('text-green-400');
            dydxBadge.textContent = 'Ready';
            dydxBadge.classList.remove('bg-red-900/50', 'text-red-300', 'border-red-700');
            dydxBadge.classList.add('bg-green-900/50', 'text-green-300', 'border-green-700');
        } else {
            dydxIndicator.classList.remove('bg-green-900');
            dydxIndicator.classList.add('bg-red-900');
            dydxIndicator.innerHTML = `
                <svg class="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                </svg>
            `;
            dydxStatusText.textContent = 'Not Configured';
            dydxStatusText.classList.remove('text-green-400');
            dydxStatusText.classList.add('text-red-400');
            dydxBadge.textContent = 'Required';
            dydxBadge.classList.remove('bg-green-900/50', 'text-green-300', 'border-green-700');
            dydxBadge.classList.add('bg-red-900/50', 'text-red-300', 'border-red-700');
        }

        // Telegram status
        const telegramIndicator = document.getElementById('telegram-indicator');
        const telegramStatusText = document.getElementById('telegram-status-text');
        const telegramBadge = document.getElementById('telegram-badge');

        if (credentialsStatus.telegram_configured) {
            telegramIndicator.classList.remove('bg-red-900');
            telegramIndicator.classList.add('bg-green-900');
            telegramIndicator.innerHTML = `
                <svg class="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
            `;
            telegramStatusText.textContent = 'Configured';
            telegramStatusText.classList.remove('text-red-400');
            telegramStatusText.classList.add('text-green-400');
            telegramBadge.textContent = 'Ready';
            telegramBadge.classList.remove('bg-yellow-900/50', 'text-yellow-300', 'border-yellow-700');
            telegramBadge.classList.add('bg-green-900/50', 'text-green-300', 'border-green-700');
        } else {
            telegramIndicator.classList.remove('bg-green-900');
            telegramIndicator.classList.add('bg-red-900');
            telegramIndicator.innerHTML = `
                <svg class="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                </svg>
            `;
            telegramStatusText.textContent = 'Not Configured';
            telegramStatusText.classList.remove('text-green-400');
            telegramStatusText.classList.add('text-red-400');
            telegramBadge.textContent = 'Optional';
            telegramBadge.classList.remove('bg-green-900/50', 'text-green-300', 'border-green-700');
            telegramBadge.classList.add('bg-yellow-900/50', 'text-yellow-300', 'border-yellow-700');
        }

        // Webhook status (already has correct icon in HTML)
        const webhookStatusText = document.getElementById('webhook-status-text');

        if (credentialsStatus.webhook_configured) {
            webhookStatusText.textContent = 'Configured';
            webhookStatusText.classList.remove('text-red-400');
            webhookStatusText.classList.add('text-green-400');
        } else {
            webhookStatusText.textContent = 'Not Configured';
            webhookStatusText.classList.remove('text-green-400');
            webhookStatusText.classList.add('text-red-400');
        }
    }

    /**
     * Show security warnings for missing credentials
     */
    showSecurityWarnings(credentialsStatus) {
        const warningsContainer = document.getElementById('security-warnings');
        warningsContainer.innerHTML = '';

        if (!credentialsStatus.dydx_configured) {
            const warning = document.createElement('div');
            warning.className = 'bg-red-900/20 border border-red-700 rounded-md p-4';
            warning.innerHTML = `
                <div class="flex">
                    <div class="flex-shrink-0">
                        <svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
                        </svg>
                    </div>
                    <div class="ml-3">
                        <h3 class="text-sm font-medium text-red-400">dYdX Credentials Required</h3>
                        <div class="mt-2 text-sm text-red-300">
                            <p>Please configure your dYdX wallet credentials to enable trading functionality.</p>
                        </div>
                    </div>
                </div>
            `;
            warningsContainer.appendChild(warning);
        }

        if (!credentialsStatus.webhook_configured) {
            const warning = document.createElement('div');
            warning.className = 'bg-yellow-900/20 border border-yellow-700 rounded-md p-4';
            warning.innerHTML = `
                <div class="flex">
                    <div class="flex-shrink-0">
                        <svg class="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
                        </svg>
                    </div>
                    <div class="ml-3">
                        <h3 class="text-sm font-medium text-yellow-400">Webhook Secret Not Configured</h3>
                        <div class="mt-2 text-sm text-yellow-300">
                            <p>Webhook secret is automatically generated. No action required unless you need to regenerate it.</p>
                        </div>
                    </div>
                </div>
            `;
            warningsContainer.appendChild(warning);
        }
    }

    /**
     * Set up event listeners for dashboard interactions
     */
    setupEventListeners() {
        // Tab switching
        this.setupTabListeners();

        // Form submissions
        this.setupFormListeners();

        // Button actions
        this.setupButtonListeners();

        // Logout functionality
        this.setupLogoutListener();
    }

    /**
     * Set up tab switching listeners
     */
    setupTabListeners() {
        const tabs = ['credentials', 'webhook', 'profile', 'equity'];

        tabs.forEach(tab => {
            const tabButton = document.getElementById(`${tab}-tab`);
            console.log('Setting up tab listener for:', tab);
            if (tabButton) {
                tabButton.addEventListener('click', () => {
                    this.showTab(tab);
                });
            }
        });
    }

    /**
     * Set up form submission listeners
     */
    setupFormListeners() {
        // dYdX credentials form
        const dydxForm = document.getElementById('dydx-form');
        if (dydxForm) {
            dydxForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.saveDydxCredentials();
            });
        }

        // Telegram credentials form
        const telegramForm = document.getElementById('telegram-form');
        if (telegramForm) {
            telegramForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.saveTelegramCredentials();
            });
        }
    }

    /**
     * Set up button action listeners
     */
    setupButtonListeners() {
        // Copy webhook URL
        const copyWebhookBtn = document.getElementById('copy-webhook-url');
        if (copyWebhookBtn) {
            copyWebhookBtn.addEventListener('click', () => {
                this.copyToClipboard('webhook-url');
            });
        }

        // Toggle webhook secret visibility
        const toggleSecretBtn = document.getElementById('toggle-secret');
        if (toggleSecretBtn) {
            toggleSecretBtn.addEventListener('click', () => {
                this.toggleSecretVisibility();
            });
        }

        // Regenerate webhook secret
        const regenerateBtn = document.getElementById('regenerate-secret');
        if (regenerateBtn) {
            regenerateBtn.addEventListener('click', () => {
                this.regenerateWebhookSecret();
            });
        }

        // Copy JSON sample
        const copyJsonBtn = document.getElementById('copy-json-sample');
        if (copyJsonBtn) {
            copyJsonBtn.addEventListener('click', () => {
                this.copyJsonSample();
            });
        }

        // Refresh balance button
        const refreshBalanceBtn = document.getElementById('refresh-balance');
        if (refreshBalanceBtn) {
            refreshBalanceBtn.addEventListener('click', async () => {
                await this.loadAccountBalance();
            });
        }
        
        // Equity curve listeners
        document.querySelectorAll('.equity-days-btn').forEach(btn => {
            btn.addEventListener('click', (event) => {
                document.querySelectorAll('.equity-days-btn').forEach(b => {
                    b.classList.remove('active', 'bg-dydx-blue', 'text-white');
                });
                event.currentTarget.classList.add('active', 'bg-dydx-blue', 'text-white');
                this.currentEquityDays = parseInt(event.currentTarget.dataset.days);
                this.fetchEquityData();
            });
        });

        const refreshEquityBtn = document.getElementById('refresh-equity');
        if (refreshEquityBtn) {
            refreshEquityBtn.addEventListener('click', () => {
                this.fetchEquityData();
                this.fetchEquitySummary();
            });
        }
    }

    // --------------------------------------------------
    // Equity Curve Methods
    // --------------------------------------------------

    formatCurrency(value) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(value);
    }

    async fetchEquityData() {
        try {
            const token = this.authToken;
            if (!token) return;

            const response = await fetch(`/api/equity/curve?days=${this.currentEquityDays}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!response.ok) throw new Error('Failed to fetch equity data');
            const data = await response.json();
            this.updateEquityCharts(data);
        } catch (error) {
            console.error('Error fetching equity data:', error);
        }
    }

    async fetchEquitySummary() {
        try {
            const token = this.authToken;
            if (!token) return;

            const response = await fetch('/api/equity/summary', {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!response.ok) throw new Error('Failed to fetch summary');
            const data = await response.json();
            this.updateEquityMetrics(data);
        } catch (error) {
            console.error('Error fetching summary:', error);
        }
    }

    updateEquityMetrics(data) {
        if (!data) return;
        document.getElementById('equity-starting').textContent = this.formatCurrency(data.starting_capital);
        document.getElementById('equity-current').textContent = this.formatCurrency(data.current_equity);
        document.getElementById('equity-growth-amount').textContent = this.formatCurrency(data.growth_amount);
        document.getElementById('equity-growth-pct').textContent = data.growth_percentage.toFixed(2) + '%';
        document.getElementById('equity-peak').textContent = this.formatCurrency(data.max_equity);
        document.getElementById('equity-drawdown').textContent = data.max_drawdown.toFixed(2) + '%';
        document.getElementById('equity-realized').textContent = this.formatCurrency(data.total_realized_pnl);
    }

    updateEquityCharts(data) {
        if (!data || !data.curve_data) return;

        const dates = data.curve_data.map(d => d.date);
        const equities = data.curve_data.map(d => d.equity);
        const growths = data.curve_data.map(d => d.growth_percentage);
        const startingCapital = data.starting_capital;
        const isProfit = equities[equities.length - 1] >= startingCapital;

        // Equity Chart
        const ctxEquity = document.getElementById('equityChart').getContext('2d');
        if (this.equityChart) this.equityChart.destroy();
        this.equityChart = new Chart(ctxEquity, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: 'Starting Capital',
                        data: Array(dates.length).fill(startingCapital),
                        borderColor: '#3b82f6',
                        borderDash: [5, 5],
                        fill: false,
                        tension: 0.1,
                        pointRadius: 0
                    },
                    {
                        label: 'Portfolio Value',
                        data: equities,
                        borderColor: isProfit ? '#10b981' : '#ef4444',
                        backgroundColor: isProfit ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointRadius: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: true, labels: { color: '#fff' } } },
                scales: {
                    y: {
                        ticks: { color: '#999', callback: v => '$' + v.toLocaleString() },
                        grid: { color: '#333' }
                    },
                    x: { ticks: { color: '#999' }, grid: { color: '#333' } }
                }
            }
        });

        // Growth Chart
        const ctxGrowth = document.getElementById('growthChart').getContext('2d');
        if (this.growthChart) this.growthChart.destroy();
        this.growthChart = new Chart(ctxGrowth, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [{
                    label: 'Growth %',
                    data: growths,
                    borderColor: isProfit ? '#10b981' : '#ef4444',
                    backgroundColor: isProfit ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: true, labels: { color: '#fff' } } },
                scales: {
                    y: {
                        ticks: { color: '#999', callback: v => v.toFixed(2) + '%' },
                        grid: { color: '#333' }
                    },
                    x: { ticks: { color: '#999' }, grid: { color: '#333' } }
                }
            }
        });
    }

    /**
     * Set up logout functionality
     */
    setupLogoutListener() {
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                this.logout();
            });
        }
    }

    /**
     * Show specific tab content
     */
    showTab(tabName) {
        // Hide all tab contents
        const contents = document.querySelectorAll('.tab-content');
        contents.forEach(content => {
            content.classList.add('hidden');
        });

        // Remove active state from all tabs
        const tabs = document.querySelectorAll('.credentials-tab, .webhook-tab, .profile-tab, .equity-tab');
        tabs.forEach(tab => {
            tab.classList.remove('border-dydx-blue', 'text-white');
            tab.classList.add('border-transparent', 'text-gray-400');
        });

        // Show selected tab content
        const selectedContent = document.getElementById(`${tabName}-content`);
        if (selectedContent) {
            selectedContent.classList.remove('hidden');
        }

        // Add active state to selected tab
        const selectedTab = document.getElementById(`${tabName}-tab`);
        if (selectedTab) {
            selectedTab.classList.remove('border-transparent', 'text-gray-400');
            selectedTab.classList.add('border-dydx-blue', 'text-white');
        }

        this.currentTab = tabName;

        // Load tab-specific data
        if (tabName === 'webhook') {
            this.loadWebhookInfo();
        } else if (tabName === 'equity') {
            this.fetchEquityData();
            this.fetchEquitySummary();
        }
    }

    /**
     * Save dYdX credentials
     */
    async saveDydxCredentials() {
        const mnemonicField = document.getElementById('dydx-mnemonic');
        const mnemonic = mnemonicField.value.trim();

        if (!mnemonic) {
            this.showError('Please enter your dYdX mnemonic phrase.');
            return;
        }

        try {
            this.showLoading('Saving dYdX credentials...');

            const response = await fetch('/api/user/credentials', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    dydx_mnemonic: mnemonic
                })
            });

            const data = await response.json();

            if (response.ok) {
                // SECURITY: Clear the mnemonic from the field immediately after saving
                mnemonicField.value = '';
                
                this.showSuccess('dYdX credentials saved and encrypted successfully!');
                await this.loadDashboardData(); // Refresh status
                await this.loadAccountBalance(); // Refresh balance
            } else {
                this.showError(data.detail || 'Failed to save dYdX credentials.');
            }

        } catch (error) {
            console.error('Save dYdX credentials error:', error);
            this.showError('Failed to save dYdX credentials. Please try again.');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * Save Telegram credentials
     */
    async saveTelegramCredentials() {
        const tokenField = document.getElementById('telegram-token');
        const chatIdField = document.getElementById('telegram-chat-id');
        const token = tokenField.value.trim();
        const chatId = chatIdField.value.trim();

        if (!token || !chatId) {
            this.showError('Please fill in both Telegram token and chat ID.');
            return;
        }

        try {
            this.showLoading('Saving Telegram settings...');

            const response = await fetch('/api/user/credentials', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    telegram_token: token,
                    telegram_chat_id: chatId
                })
            });

            const data = await response.json();

            if (response.ok) {
                // SECURITY: Clear the credentials from fields immediately after saving
                tokenField.value = '';
                chatIdField.value = '';
                
                this.showSuccess('Telegram settings saved and encrypted successfully!');
                await this.loadDashboardData(); // Refresh status
            } else {
                this.showError(data.detail || 'Failed to save Telegram settings.');
            }

        } catch (error) {
            console.error('Save Telegram credentials error:', error);
            this.showError('Failed to save Telegram settings. Please try again.');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * Load webhook information
     */
    async loadWebhookInfo() {
        try {
            const response = await fetch('/api/user/webhook-info', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json',
                }
            });

            if (response.status === 401) {
                this.redirectToLogin();
                return;
            }

            const data = await response.json();

            if (response.ok) {
                document.getElementById('webhook-url').value = data.webhook_url || '';
                document.getElementById('webhook-secret').value = data.webhook_secret || '';
            } else {
                this.showError(data.detail || 'Failed to load webhook information.');
            }

        } catch (error) {
            console.error('Load webhook info error:', error);
            this.showError('Failed to load webhook information.');
        }
    }

    /**
     * Load account balance from dYdX
     */
    async loadAccountBalance() {
        const balanceLoading = document.getElementById('balance-loading');
        const balanceValue = document.getElementById('balance-value');
        const balanceIndicator = document.getElementById('balance-indicator');
        const balanceText = document.getElementById('balance-text');

        try {
            // Show loading state
            if (balanceLoading) balanceLoading.classList.remove('hidden');
            if (balanceValue) balanceValue.classList.add('hidden');

            const response = await fetch('/api/user/account-balance', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json',
                }
            });

            if (response.status === 401) {
                this.redirectToLogin();
                return;
            }

            const data = await response.json();

            if (response.ok && data.success) {
                // Update main balance card
                const equity = parseFloat(data.equity || 0);
                if (balanceValue) {
                    balanceValue.textContent = `$${equity.toLocaleString('en-US', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    })}`;
                    balanceValue.classList.remove('hidden');
                }
                if (balanceLoading) balanceLoading.classList.add('hidden');

                // Update indicator color based on balance
                if (balanceIndicator) {
                    balanceIndicator.classList.remove('bg-gray-700', 'bg-green-900', 'bg-yellow-900');
                    if (equity > 0) {
                        balanceIndicator.classList.add('bg-green-900');
                        balanceIndicator.innerHTML = `
                            <svg class="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                        `;
                    } else {
                        balanceIndicator.classList.add('bg-yellow-900');
                        balanceIndicator.innerHTML = `
                            <svg class="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                            </svg>
                        `;
                    }
                }

                if (balanceText) {
                    balanceText.classList.remove('text-gray-400');
                    balanceText.classList.add('text-white');
                }

                // Update profile tab balance details
                const profileEquity = document.getElementById('profile-equity');
                const profileFreeCollateral = document.getElementById('profile-free-collateral');
                const profileMarginUsed = document.getElementById('profile-margin-used');
                const profilePositionsValue = document.getElementById('profile-positions-value');
                const balanceError = document.getElementById('balance-error');

                if (profileEquity) {
                    profileEquity.textContent = `$${equity.toLocaleString('en-US', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    })}`;
                }

                if (profileFreeCollateral) {
                    const freeCollateral = parseFloat(data.free_collateral || 0);
                    profileFreeCollateral.textContent = `$${freeCollateral.toLocaleString('en-US', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    })}`;
                }

                if (profileMarginUsed) {
                    const marginUsed = parseFloat(data.margin_used || 0);
                    profileMarginUsed.textContent = `$${marginUsed.toLocaleString('en-US', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    })}`;
                }

                if (profilePositionsValue) {
                    const positionsValue = parseFloat(data.open_positions_value || 0);
                    profilePositionsValue.textContent = `$${positionsValue.toLocaleString('en-US', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    })}`;
                }

                if (balanceError) {
                    balanceError.classList.add('hidden');
                }

            } else {
                // Show error state
                if (balanceLoading) {
                    balanceLoading.textContent = 'N/A';
                }
                if (balanceIndicator) {
                    balanceIndicator.classList.remove('bg-green-900', 'bg-yellow-900');
                    balanceIndicator.classList.add('bg-gray-700');
                    balanceIndicator.innerHTML = `
                        <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                    `;
                }

                // Show error in profile tab
                const balanceError = document.getElementById('balance-error');
                if (balanceError) {
                    balanceError.textContent = data.error || 'Configure dYdX credentials to view balance';
                    balanceError.classList.remove('hidden');
                }
            }

        } catch (error) {
            console.error('Load account balance error:', error);
            
            // Show error state
            if (balanceLoading) {
                balanceLoading.textContent = 'Error';
            }
            
            const balanceError = document.getElementById('balance-error');
            if (balanceError) {
                balanceError.textContent = 'Failed to load balance. Please try again.';
                balanceError.classList.remove('hidden');
            }
        }
    }

    /**
     * Regenerate webhook secret
     */
    async regenerateWebhookSecret() {
        if (!confirm('Are you sure you want to regenerate the webhook secret? You will need to update any services using the old secret.')) {
            return;
        }

        try {
            this.showLoading('Regenerating webhook secret...');

            const response = await fetch('/api/user/webhook-secret', {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json',
                }
            });

            const data = await response.json();

            if (response.ok) {
                this.showSuccess('Webhook secret regenerated successfully!');
                await this.loadWebhookInfo(); // Refresh webhook info
            } else {
                this.showError(data.detail || 'Failed to regenerate webhook secret.');
            }

        } catch (error) {
            console.error('Regenerate webhook secret error:', error);
            this.showError('Failed to regenerate webhook secret. Please try again.');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * Copy text to clipboard
     */
    copyToClipboard(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.select();
            document.execCommand('copy');

            // Show feedback
            this.showSuccess('Copied to clipboard!');
        }
    }
    /**
     * Copy JSON sample to clipboard
     */
    copyJsonSample() {
        const jsonSample = document.getElementById('json-sample');
        if (jsonSample) {
            const text = jsonSample.textContent;
            
            // Create temporary textarea for copying
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);

            // Show feedback
            this.showSuccess('JSON sample copied to clipboard!');
        }
    }


    /**
     * Toggle webhook secret visibility
     */
    toggleSecretVisibility() {
        const secretInput = document.getElementById('webhook-secret');
        const toggleBtn = document.getElementById('toggle-secret');

        if (secretInput.type === 'password') {
            secretInput.type = 'text';
            toggleBtn.textContent = 'Hide';
        } else {
            secretInput.type = 'password';
            toggleBtn.textContent = 'Show';
        }
    }

    /**
     * Update user address display
     */
    updateUserAddress() {
        const addressElement = document.getElementById('user-address');
        if (addressElement && this.userAddress) {
            addressElement.textContent = `Wallet: ${this.userAddress.slice(0, 6)}...${this.userAddress.slice(-4)}`;
        }
    }

    /**
     * Logout user
     */
    async logout() {
        try {
            // Call logout endpoint
            await fetch('/api/auth/logout', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json',
                }
            });
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            // Clear local storage
            sessionStorage.removeItem('auth_token');
            sessionStorage.removeItem('user_address');

            // Redirect to login
            window.location.href = '/login';
        }
    }

    /**
     * Show loading state
     */
    showLoading(message = 'Loading...') {
        // Create or update loading overlay
        let overlay = document.getElementById('loading-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'loading-overlay';
            overlay.className = 'fixed inset-0 bg-gray-900/50 backdrop-blur-sm flex items-center justify-center z-50';
            overlay.innerHTML = `
                <div class="bg-gray-800 rounded-lg p-6 flex items-center space-x-4">
                    <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-dydx-blue"></div>
                    <span class="text-white">${message}</span>
                </div>
            `;
            document.body.appendChild(overlay);
        } else {
            overlay.querySelector('span').textContent = message;
            overlay.classList.remove('hidden');
        }
    }

    /**
     * Hide loading state
     */
    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.classList.add('hidden');
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = 'fixed top-4 right-4 bg-red-900/90 border border-red-700 rounded-md p-4 z-50 max-w-sm';
        toast.innerHTML = `
            <div class="flex">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
                    </svg>
                </div>
                <div class="ml-3">
                    <p class="text-sm text-red-300">${message}</p>
                </div>
            </div>
        `;

        document.body.appendChild(toast);

        // Remove after 5 seconds
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }

    /**
     * Show success message
     */
    showSuccess(message = 'Success!') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = 'fixed top-4 right-4 bg-green-900/90 border border-green-700 rounded-md p-4 z-50 max-w-sm';
        toast.innerHTML = `
            <div class="flex">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                    </svg>
                </div>
                <div class="ml-3">
                    <p class="text-sm text-green-300">${message}</p>
                </div>
            </div>
        `;

        document.body.appendChild(toast);

        // Remove after 3 seconds
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    /**
     * Redirect to login page
     */
    redirectToLogin() {
        window.location.href = '/login';
    }


}