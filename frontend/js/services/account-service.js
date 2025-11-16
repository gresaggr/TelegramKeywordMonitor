// frontend/js/services/account-service.js
const accountService = {
    async getAccounts() {
        return apiClient.call('/accounts/');
    },

    async createAccount(data) {
        return apiClient.call('/accounts/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async updateAccount(id, data) {
        return apiClient.call(`/accounts/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    },

    async verifyCode(accountId, code, twoFaPassword = null) {
        return apiClient.call('/accounts/verify-code', {
            method: 'POST',
            body: JSON.stringify({
                account_id: accountId,
                code: code,
                two_fa_password: twoFaPassword
            })
        });
    },

    async deleteAccount(id) {
        return apiClient.call(`/accounts/${id}`, {
            method: 'DELETE'
        });
    },

    async startAccount(id) {
        return apiClient.call(`/accounts/${id}/start`, {
            method: 'POST'
        });
    },

    async stopAccount(id) {
        return apiClient.call(`/accounts/${id}/stop`, {
            method: 'POST'
        });
    },

    async getNotifications(id) {
        return apiClient.call(`/accounts/${id}/notifications`);
    },

    async markNotificationRead(accountId, notificationId) {
        return apiClient.call(`/accounts/${accountId}/notifications/${notificationId}/read`, {
            method: 'POST'
        });
    }
};