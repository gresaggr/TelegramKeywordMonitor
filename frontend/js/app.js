// frontend/js/app.js
const {createApp} = Vue;

// Translation helper
window.currentLanguage = 'en';
window.t = function (key) {
    const lang = window.currentLanguage || 'en';
    return translations[lang] && translations[lang][key] ? translations[lang][key] : key;
};

window.setLanguage = function (lang) {
    window.currentLanguage = lang;
    localStorage.setItem('language', lang);
    // Trigger Vue reactivity
    if (window.vueApp) {
        window.vueApp.$forceUpdate();
    }
};

const app = createApp({
    components: {
        'login-component': LoginComponent,
        'register-component': RegisterComponent,
        'telegram-dashboard-component': TelegramDashboardComponent
    },
    data() {
        return {
            isLoading: true,
            isAuthenticated: false,
            showRegister: false,
            loading: false,
            error: '',
            user: null,
            accounts: [],
            languageTrigger: 0
        };
    },
    async mounted() {
        window.vueApp = this;

        // Load language from localStorage or user profile
        const savedLang = localStorage.getItem('language');
        if (savedLang) {
            window.setLanguage(savedLang);
        }

        await this.checkAuth();
        if (this.isAuthenticated) {
            setInterval(() => this.loadAccounts(), 30000);
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

                    // Set language from user profile
                    if (this.user && this.user.language) {
                        window.setLanguage(this.user.language);
                        this.languageTrigger++;
                    }
                } catch (err) {
                    console.error('Auth check failed:', err);
                    localStorage.removeItem('token');
                    this.isAuthenticated = false;
                }
            }
            this.isLoading = false;
        },

        async loadUserData() {
            this.user = await authService.getCurrentUser();
        },

        async loadAccounts() {
            try {
                this.accounts = await accountService.getAccounts();
            } catch (err) {
                console.error('Failed to load accounts:', err);
                this.accounts = [];
            }
        },

        async handleLogin(credentials) {
            this.error = '';
            this.loading = true;
            try {
                const data = await authService.login(credentials.email, credentials.password);
                localStorage.setItem('token', data.access_token);
                await this.loadUserData();
                await this.loadAccounts();
                this.isAuthenticated = true;

                // Set language from user profile
                if (this.user && this.user.language) {
                    window.setLanguage(this.user.language);
                    this.languageTrigger++;
                }
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
                await authService.register(credentials.email, credentials.username, credentials.password);
                const loginData = await authService.login(credentials.email, credentials.password);
                localStorage.setItem('token', loginData.access_token);
                await this.loadUserData();
                await this.loadAccounts();
                this.isAuthenticated = true;

                // Set language from user profile
                if (this.user && this.user.language) {
                    window.setLanguage(this.user.language);
                    this.languageTrigger++;
                }
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
            window.setLanguage('en');
            this.languageTrigger++;
        },

        async handleAddAccount(data) {
            try {
                const account = await accountService.createAccount(data);
                await this.loadAccounts();

                if (account.status === 'awaiting_code' || account.status === 'awaiting_2fa') {
                    uiHelpers.showToast('Account created! Please verify the code sent to your phone.');
                } else {
                    uiHelpers.showToast('Account added and monitoring started!');
                }
            } catch (err) {
                alert('Failed to add account: ' + err.message);
            }
        },

        async handleDeleteAccount(id) {
            try {
                await accountService.deleteAccount(id);
                await this.loadAccounts();
                uiHelpers.showToast('Account deleted successfully!');
            } catch (err) {
                alert('Failed to delete account: ' + err.message);
            }
        },

        async handleStopAccount(id) {
            try {
                await accountService.stopAccount(id);
                await this.loadAccounts();
                uiHelpers.showToast('Account monitoring stopped!');
            } catch (err) {
                alert('Failed to stop account: ' + err.message);
            }
        },

        async handleStartAccount(id) {
            try {
                await accountService.startAccount(id);
                await this.loadAccounts();
                uiHelpers.showToast('Account monitoring started!');
            } catch (err) {
                alert('Failed to start account: ' + err.message);
            }
        },

        async handleReloadUser() {
            try {
                await this.loadUserData();
                if (this.user && this.user.language) {
                    window.setLanguage(this.user.language);
                    this.languageTrigger++;
                }
            } catch (err) {
                console.error('Failed to reload user data:', err);
            }
        },

        async handleReloadAccounts() {
            await this.loadAccounts();
        }
    }
});

app.mount('#app');