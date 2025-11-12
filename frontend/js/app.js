const {createApp} = Vue;

createApp({
    components: {
        'login-component': LoginComponent,
        'register-component': RegisterComponent,
        'telegram-dashboard-component': TelegramDashboardComponent,
        'account-modal-component': AccountModalComponent,
        'verify-code-modal-component': VerifyCodeModalComponent,
    },
    data() {
        return {
            isLoading: true,
            isAuthenticated: false,
            showRegister: false,
            loading: false,
            error: '',
            user: null,
            accounts: []
        };
    },
    async mounted() {
        await this.checkAuth();
        // Auto-refresh accounts every 30 seconds
        if (this.isAuthenticated) {
            setInterval(() => {
                this.loadAccounts();
            }, 30000);
        }
    },
    methods: {
        async checkAuth() {
            const token = localStorage.getItem('token');
            if (token) {
                try {
                    await this.loadUserData();
                    await this.loadAccounts();
                    this.isAuthenticated = true;
                } catch (err) {
                    console.error('Auth check failed:', err);
                    localStorage.removeItem('token');
                    this.isAuthenticated = false;
                }
            }
            this.isLoading = false;
        },

        async loadUserData() {
            try {
                this.user = await api.getCurrentUser();
            } catch (err) {
                console.error('Failed to load user data:', err);
                throw err;
            }
        },

        async loadAccounts() {
            try {
                this.accounts = await api.getTelegramAccounts();
            } catch (err) {
                console.error('Failed to load accounts:', err);
                this.accounts = [];
            }
        },

        async handleLogin(credentials) {
            this.error = '';
            this.loading = true;

            try {
                const data = await api.login(credentials.email, credentials.password);
                localStorage.setItem('token', data.access_token);
                await this.loadUserData();
                await this.loadAccounts();
                this.isAuthenticated = true;
            } catch (err) {
                this.error = err.message || 'Login failed';
            } finally {
                this.loading = false;
            }
        },

        async handleRegister(credentials) {
            this.error = '';
            this.loading = true;

            try {
                await api.register(credentials.email, credentials.username, credentials.password);
                const loginData = await api.login(credentials.email, credentials.password);
                localStorage.setItem('token', loginData.access_token);
                await this.loadUserData();
                await this.loadAccounts();
                this.isAuthenticated = true;
            } catch (err) {
                this.error = err.message || 'Registration failed';
            } finally {
                this.loading = false;
            }
        },

        handleLogout() {
            localStorage.removeItem('token');
            this.isAuthenticated = false;
            this.user = null;
            this.accounts = [];
            this.error = '';
        },

        async handleAddAccount(data) {
            try {
                const account = await api.createTelegramAccount(data);
                await this.loadAccounts();

                // If account needs verification, show success message
                if (account.status === 'awaiting_code' || account.status === 'awaiting_2fa') {
                    this.showSuccess('Account created! Please verify the code sent to your phone.');
                } else {
                    this.showSuccess('Account added and monitoring started!');
                }
            } catch (err) {
                alert('Failed to add account: ' + err.message);
            }
        },

        async handleEditAccount(id, data) {
            try {
                await api.updateTelegramAccount(id, data);
                await this.loadAccounts();
                this.showSuccess('Account updated successfully!');
            } catch (err) {
                alert('Failed to update account: ' + err.message);
            }
        },

        async handleDeleteAccount(id) {
            try {
                await api.deleteTelegramAccount(id);
                await this.loadAccounts();
                this.showSuccess('Account deleted successfully!');
            } catch (err) {
                alert('Failed to delete account: ' + err.message);
            }
        },

        async handleStopAccount(id) {
            try {
                await api.stopTelegramAccount(id);
                await this.loadAccounts();
                this.showSuccess('Account monitoring stopped!');
            } catch (err) {
                alert('Failed to stop account: ' + err.message);
            }
        },

        async handleStartAccount(id) {
            try {
                await api.startTelegramAccount(id);
                await this.loadAccounts();
                this.showSuccess('Account monitoring started!');
            } catch (err) {
                alert('Failed to start account: ' + err.message);
            }
        },

        async handleReloadUser() {
            try {
                await this.loadUserData();
            } catch (err) {
                console.error('Failed to reload user data:', err);
            }
        },

        async handleReloadAccounts() {
            await this.loadAccounts();
        },

        showSuccess(message) {
            const toast = document.createElement('div');
            toast.className = 'alert alert-success';
            toast.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; animation: slideDown 0.3s ease; min-width: 300px;';
            toast.innerHTML = `
                <svg style="width: 20px; height: 20px; flex-shrink: 0;" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
                <span>${message}</span>
            `;
            document.body.appendChild(toast);

            setTimeout(() => {
                toast.remove();
            }, 3000);
        }
    }
}).mount('#app');