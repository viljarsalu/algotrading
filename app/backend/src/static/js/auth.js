/**
 * Web3 Authentication Module
 *
 * Handles wallet connection, message signing, and authentication flow
 * for the dYdX Trading Service login page.
 */

// Web3 and authentication utilities
class Web3AuthManager {
    constructor() {
        this.isConnected = false;
        this.currentAccount = null;
        this.chainId = null;
        this.web3Modal = null;
        this.provider = null;

        // Initialize if MetaMask is available
        if (typeof window.ethereum !== 'undefined') {
            this.provider = window.ethereum;
            this.setupEventListeners();
        }

        // Update connection status on page load
        this.updateConnectionStatus();
    }

    /**
     * Set up event listeners for wallet events
     */
    setupEventListeners() {
        if (this.provider) {
            this.provider.on('accountsChanged', (accounts) => {
                if (accounts.length > 0) {
                    this.currentAccount = accounts[0];
                    this.updateUI();
                } else {
                    this.disconnect();
                }
            });

            this.provider.on('chainChanged', (chainId) => {
                this.chainId = parseInt(chainId, 16);
                this.updateNetworkInfo();
            });
        }
    }

    /**
     * Check if MetaMask or other Web3 wallet is available
     */
    isWeb3Available() {
        return typeof window.ethereum !== 'undefined';
    }

    /**
     * Connect to MetaMask wallet
     */
    async connectWallet() {
        if (!this.isWeb3Available()) {
            this.showError('MetaMask not detected. Please install MetaMask to continue.');
            return false;
        }

        try {
            this.showLoading('Connecting to wallet...');

            // Request account access
            const accounts = await this.provider.request({
                method: 'eth_requestAccounts'
            });

            if (accounts.length > 0) {
                this.currentAccount = accounts[0];
                this.isConnected = true;

                // Get chain ID
                const chainId = await this.provider.request({
                    method: 'eth_chainId'
                });
                this.chainId = parseInt(chainId, 16);

                this.updateUI();
                this.hideLoading();
                return true;
            }

        } catch (error) {
            console.error('Wallet connection error:', error);
            this.hideLoading();

            if (error.code === 4001) {
                this.showError('Connection rejected by user.');
            } else if (error.code === -32002) {
                this.showError('Connection request already pending. Check MetaMask.');
            } else {
                this.showError('Failed to connect wallet. Please try again.');
            }
        }

        return false;
    }

    /**
     * Disconnect wallet
     */
    disconnect() {
        this.isConnected = false;
        this.currentAccount = null;
        this.chainId = null;
        this.updateUI();
    }

    /**
     * Switch to Ethereum mainnet
     */
    async switchToMainnet() {
        if (!this.provider) return false;

        try {
            await this.provider.request({
                method: 'wallet_switchEthereumChain',
                params: [{ chainId: '0x1' }], // Ethereum mainnet
            });
            return true;
        } catch (error) {
            // Error code 4902 means the chain hasn't been added to MetaMask
            if (error.code === 4902) {
                try {
                    await this.provider.request({
                        method: 'wallet_addEthereumChain',
                        params: [{
                            chainId: '0x1',
                            chainName: 'Ethereum Mainnet',
                            nativeCurrency: {
                                name: 'Ether',
                                symbol: 'ETH',
                                decimals: 18,
                            },
                            rpcUrls: ['https://mainnet.infura.io/v3/'],
                            blockExplorerUrls: ['https://etherscan.io/'],
                        }],
                    });
                    return true;
                } catch (addError) {
                    console.error('Failed to add Ethereum chain:', addError);
                    return false;
                }
            }
            console.error('Failed to switch network:', error);
            return false;
        }
    }

    /**
      * Request signature for authentication
      */
     async requestSignature() {
         console.log('requestSignature called, connected:', this.isConnected, 'account:', this.currentAccount);

         if (!this.isConnected || !this.currentAccount) {
             this.showError('Wallet not connected.');
             return null;
         }

         // Check if we're on the correct network
         if (this.chainId !== 1) {
             this.showError('Please switch to Ethereum Mainnet to continue.');
             const switched = await this.switchToMainnet();
             if (!switched) return null;
         }

         try {
             console.log('Requesting signature...');
             this.showLoading('Requesting signature...');

             // Generate authentication message
             const message = this.generateAuthMessage();
             console.log('Generated message:', message);
             this.displayMessage(message);

             // Request signature
             console.log('Calling personal_sign...');
             const signature = await this.provider.request({
                 method: 'personal_sign',
                 params: [message, this.currentAccount],
             });

             console.log('Got signature:', signature ? 'SUCCESS' : 'EMPTY');
             this.hideLoading();
             return {
                 signature: signature,
                 message: message,
                 address: this.currentAccount
             };

         } catch (error) {
             console.error('Signature request error:', error);
             this.hideLoading();

             if (error.code === 4001) {
                 this.showError('Signature rejected by user.');
             } else {
                 this.showError('Failed to request signature. Please try again.');
             }
             return null;
         }
     }

    /**
     * Generate authentication message
     */
    generateAuthMessage() {
        const timestamp = Date.now();
        const nonce = Math.random().toString(36).substring(2, 15);

        return `dYdX Trading Service Authentication

Wallet: ${this.currentAccount}
Nonce: ${nonce}
Timestamp: ${timestamp}

Sign this message to authenticate with your dYdX Trading Service account. This request will not trigger any blockchain transaction or cost any gas fees.`;
    }

    /**
      * Authenticate with backend API
      */
     async authenticate(signatureData) {
         let timeoutId = null;

         try {
             console.log('Starting authentication for:', signatureData.address);
             this.showLoading('Authenticating...');

             const controller = new AbortController();

             // Set up timeout with more robust safety check
             timeoutId = setTimeout(() => {
                 // Double-check that timeout still exists and controller isn't aborted
                 if (timeoutId && !controller.signal.aborted) {
                     console.log('Authentication timeout reached, aborting request');
                     controller.abort();
                 }
             }, 10000); // 10 second timeout

             const response = await fetch('/api/auth/login', {
                 method: 'POST',
                 headers: {
                     'Content-Type': 'application/json',
                 },
                 body: JSON.stringify({
                     wallet_address: signatureData.address,
                     message: signatureData.message,
                     signature: signatureData.signature
                 }),
                 signal: controller.signal
             });

             // Clear timeout immediately when request completes
             if (timeoutId) {
                 clearTimeout(timeoutId);
                 timeoutId = null;
             }

             console.log('Auth response status:', response.status);
             const data = await response.json();
             console.log('Auth response data:', data);

             if (response.ok) {
                 // Store authentication token
                 sessionStorage.setItem('auth_token', data.access_token);
                 sessionStorage.setItem('user_address', signatureData.address);

                 this.showSuccess();
                 return true;
             } else {
                 console.error('Auth failed with status:', response.status, 'data:', data);
                 this.showError(data.detail || 'Authentication failed.');
                 return false;
             }

         } catch (error) {
             console.error('Authentication error:', error);

             // Don't show error if operation was aborted by user navigation or timeout cleanup
             if (error.name === 'AbortError') {
                 console.log('Authentication aborted - likely due to timeout or user navigation');
                 return false;
             }

             this.showError('Authentication failed. Please check your connection and try again.');
             return false;
         } finally {
             // Final cleanup - ensure timeout is cleared
             if (timeoutId) {
                 clearTimeout(timeoutId);
                 timeoutId = null;
             }
             this.hideLoading();
         }
     }

    /**
     * Create new user account
     */
     async createUser(signatureData) {
        let timeoutId = null;

        try {
            this.showLoading('Creating account...');

            // First, get the backend-generated message for this wallet
            console.log('Getting backend-generated message for user creation...');
            const messageResponse = await fetch(`/api/auth/generate-message?wallet_address=${encodeURIComponent(signatureData.address)}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (!messageResponse.ok) {
                throw new Error('Failed to get message for user creation');
            }

            const messageData = await messageResponse.json();
            const backendMessage = messageData.message;

            console.log('Backend message for user creation:', backendMessage);

            // Now sign the backend-generated message
            console.log('Requesting signature for backend message...');
            const backendSignatureData = await this.requestSignatureForMessage(backendMessage);

            if (!backendSignatureData) {
                throw new Error('Failed to sign backend message');
            }

            const controller = new AbortController();

            // Set up timeout with more robust safety check
            timeoutId = setTimeout(() => {
                // Double-check that timeout still exists and controller isn't aborted
                if (timeoutId && !controller.signal.aborted) {
                    console.log('Account creation timeout reached, aborting request');
                    controller.abort();
                }
            }, 10000); // 10 second timeout

            const response = await fetch('/api/auth/create-user', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    wallet_address: backendSignatureData.address,
                    message: backendMessage,
                    signature: backendSignatureData.signature
                }),
                signal: controller.signal
            });

            // Clear timeout immediately when request completes
            if (timeoutId) {
                clearTimeout(timeoutId);
                timeoutId = null;
            }

            const data = await response.json();

            if (response.ok) {
                this.showSuccess('Account created successfully!');
                return true;
            } else {
                this.showError(data.detail || 'Account creation failed.');
                return false;
            }

        } catch (error) {
            console.error('Account creation error:', error);

            // Don't show error if operation was aborted by timeout or user navigation
            if (error.name === 'AbortError') {
                console.log('Account creation aborted - likely due to timeout or user navigation');
                return false;
            }

            this.showError('Account creation failed. Please try again.');
            return false;
        } finally {
            // Final cleanup - ensure timeout is cleared
            if (timeoutId) {
                clearTimeout(timeoutId);
                timeoutId = null;
            }
            this.hideLoading();
        }
    }

    /**
     * Request signature for a specific message
     */
    async requestSignatureForMessage(message) {
        if (!this.isConnected || !this.currentAccount) {
            this.showError('Wallet not connected.');
            return null;
        }

        try {
            console.log('Requesting signature for backend message...');

            // Request signature for the backend-generated message
            const signature = await this.provider.request({
                method: 'personal_sign',
                params: [message, this.currentAccount],
            });

            console.log('Got signature for backend message:', signature ? 'SUCCESS' : 'EMPTY');
            return {
                signature: signature,
                message: message,
                address: this.currentAccount
            };

        } catch (error) {
            console.error('Backend signature request error:', error);
            if (error.code === 4001) {
                this.showError('Signature rejected by user.');
            } else {
                this.showError('Failed to request signature. Please try again.');
            }
            return null;
        }
    }

    /**
     * Update connection status in UI
     */
    updateConnectionStatus() {
        if (this.isWeb3Available()) {
            this.updateNetworkInfo();
        } else {
            document.getElementById('network-status').textContent = 'MetaMask Required';
            document.getElementById('chain-id').textContent = 'Install MetaMask';
        }
    }

    /**
     * Update network information in UI
     */
    updateNetworkInfo() {
        if (this.chainId === 1) {
            document.getElementById('network-status').textContent = 'Ethereum Mainnet';
            document.getElementById('chain-id').textContent = '1';
        } else if (this.chainId === 11155111) {
            document.getElementById('network-status').textContent = 'Sepolia Testnet';
            document.getElementById('chain-id').textContent = '11155111';
        } else {
            document.getElementById('network-status').textContent = 'Unsupported Network';
            document.getElementById('chain-id').textContent = this.chainId || 'Unknown';
        }
    }

    /**
     * Update UI based on connection state
     */
    updateUI() {
        const connectBtn = document.getElementById('connect-wallet-btn');
        const connectionStatus = document.getElementById('connection-status');
        const connectedAddress = document.getElementById('connected-address');
        const signingSection = document.getElementById('signing-section');

        if (this.isConnected && this.currentAccount) {
            // Show connected state
            connectBtn.textContent = 'Wallet Connected';
            connectBtn.classList.remove('bg-dydx-blue', 'hover:bg-dydx-blue-dark');
            connectBtn.classList.add('bg-green-600', 'hover:bg-green-700');

            // Show connection status
            connectionStatus.classList.remove('hidden');
            connectedAddress.textContent = `${this.currentAccount.slice(0, 6)}...${this.currentAccount.slice(-4)}`;

            // Show signing section
            signingSection.classList.remove('hidden');

            this.updateNetworkInfo();
        } else {
            // Show disconnected state
            connectBtn.textContent = 'Connect MetaMask Wallet';
            connectBtn.classList.remove('bg-green-600', 'hover:bg-green-700');
            connectBtn.classList.add('bg-dydx-blue', 'hover:bg-dydx-blue-dark');

            // Hide connection status
            connectionStatus.classList.add('hidden');

            // Hide signing section
            signingSection.classList.add('hidden');
        }
    }

    /**
     * Display message for signing
     */
    displayMessage(message) {
        document.getElementById('message-text').textContent = message;
    }

    /**
     * Show loading state
     */
    showLoading(text = 'Loading...') {
        const loadingSection = document.getElementById('loading-section');
        const loadingText = document.getElementById('loading-text');

        loadingText.textContent = text;
        loadingSection.classList.remove('hidden');
    }

    /**
     * Hide loading state
     */
    hideLoading() {
        document.getElementById('loading-section').classList.add('hidden');
    }

    /**
     * Show error message
     */
    showError(message) {
        const errorSection = document.getElementById('error-section');
        const errorMessage = document.getElementById('error-message');

        errorMessage.textContent = message;
        errorSection.classList.remove('hidden');

        // Hide after 5 seconds
        setTimeout(() => {
            errorSection.classList.add('hidden');
        }, 5000);
    }

    /**
     * Show success state
     */
    showSuccess(message = 'Success!') {
        const successSection = document.getElementById('success-section');

        // Update success message if provided
        if (message !== 'Success!') {
            const successMessage = successSection.querySelector('p');
            if (successMessage) {
                successMessage.textContent = message;
            }
        }

        successSection.classList.remove('hidden');

        // Redirect to dashboard after 2 seconds
        setTimeout(() => {
            window.location.href = '/dashboard';
        }, 2000);
    }
}

// Global authentication manager instance
let authManager;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    authManager = new Web3AuthManager();

    // Set up event listeners
    setupEventListeners();
});

/**
 * Set up UI event listeners
 */
function setupEventListeners() {
    // Connect wallet button
    const connectBtn = document.getElementById('connect-wallet-btn');
    if (connectBtn) {
        connectBtn.addEventListener('click', async () => {
            const connected = await authManager.connectWallet();
            if (connected) {
                authManager.updateUI();
            }
        });
    }

    // Sign message button
    const signBtn = document.getElementById('sign-message-btn');
    if (signBtn) {
        signBtn.addEventListener('click', async () => {
            const signatureData = await authManager.requestSignature();
            if (signatureData) {
                // Try to authenticate first
                const authenticated = await authManager.authenticate(signatureData);
                if (!authenticated) {
                    // If authentication fails, offer to create account
                    const createAccount = confirm('Authentication failed. Would you like to create a new account?');
                    if (createAccount) {
                        await authManager.createUser(signatureData);
                    }
                }
            }
        });
    }
}

// Utility functions for external use
window.Web3AuthManager = Web3AuthManager;