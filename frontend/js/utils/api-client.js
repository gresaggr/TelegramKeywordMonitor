// frontend/js/utils/api-client.js
const API_URL = 'http://localhost:8000/api/v1';

class ApiClient {
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
    }
}

const apiClient = new ApiClient();