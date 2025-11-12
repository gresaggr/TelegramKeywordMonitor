const API_URL = 'http://localhost:8000/api/v1';

const api = {
    async call(endpoint, options = {}) {
        const token = localStorage.getItem('token');
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (token && !options.skipAuth) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const response = await axios({
                url: `${API_URL}${endpoint}`,
                method: options.method || 'GET',
                headers,
                data: options.body ? JSON.parse(options.body) : undefined
            });
            return response.data;
        } catch (error) {
            const message = error.response?.data?.detail || error.message || 'Request failed';
            throw new Error(message);
        }
    },

    // Auth
    async login(email, password) {
        return this.call('/auth/login/', {
            method: 'POST',
            body: JSON.stringify({email, password}),
            skipAuth: true
        });
    },

    async register(email, username, password) {
        return this.call('/auth/register/', {
            method: 'POST',
            body: JSON.stringify({email, username, password}),
            skipAuth: true
        });
    },

    async getCurrentUser() {
        return this.call('/auth/me');
    },

    async updateProfile(data) {
        return this.call('/auth/me', {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    },

    // Balance
    async getBalance() {
        return this.call('/balance/');
    },

    async topupBalance(amount) {
        return this.call('/balance/topup', {
            method: 'POST',
            body: JSON.stringify({amount})
        });
    },

    // Telegram Accounts
    async getTelegramAccounts() {
        return this.call('/accounts/');
    },

    async createTelegramAccount(data) {
        return this.call('/accounts/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async verifyCode(accountId, code, twoFaPassword = null) {
        return this.call('/accounts/verify-code', {
            method: 'POST',
            body: JSON.stringify({
                account_id: accountId,
                code: code,
                two_fa_password: twoFaPassword
            })
        });
    },

    async updateTelegramAccount(id, data) {
        return this.call(`/accounts/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    },

    async deleteTelegramAccount(id) {
        return this.call(`/accounts/${id}`, {
            method: 'DELETE'
        });
    },

    async startTelegramAccount(id) {
        return this.call(`/accounts/${id}/start`, {
            method: 'POST'
        });
    },

    async stopTelegramAccount(id) {
        return this.call(`/accounts/${id}/stop`, {
            method: 'POST'
        });
    },

    async getAccountNotifications(id) {
        return this.call(`/accounts/${id}/notifications`);
    },

    async markNotificationRead(accountId, notificationId) {
        return this.call(`/accounts/${accountId}/notifications/${notificationId}/read`, {
            method: 'POST'
        });
    }
};