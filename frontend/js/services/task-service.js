// frontend/js/services/task-service.js
const taskService = {
    async createTask(accountId, data) {
        return apiClient.call(`/accounts/${accountId}/tasks`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async updateTask(accountId, taskId, data) {
        return apiClient.call(`/accounts/${accountId}/tasks/${taskId}`, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    },

    async startTask(accountId, taskId) {
        return apiClient.call(`/accounts/${accountId}/tasks/${taskId}/start`, {
            method: 'POST'
        });
    },

    async stopTask(accountId, taskId) {
        return apiClient.call(`/accounts/${accountId}/tasks/${taskId}/stop`, {
            method: 'POST'
        });
    },

    async deleteTask(accountId, taskId) {
        return apiClient.call(`/accounts/${accountId}/tasks/${taskId}`, {
            method: 'DELETE'
        });
    }
};