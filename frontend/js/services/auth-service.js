// frontend/js/services/auth-service.js
const authService = {
    async login(email, password) {
        return apiClient.call('/auth/login/', {
            method: 'POST',
            body: JSON.stringify({email, password}),
            skipAuth: true
        });
    },

    async register(email, username, password) {
        return apiClient.call('/auth/register/', {
            method: 'POST',
            body: JSON.stringify({email, username, password}),
            skipAuth: true
        });
    },

    async getCurrentUser() {
        return apiClient.call('/auth/me');
    },

    async updateProfile(data) {
        return apiClient.call('/auth/me', {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }
};