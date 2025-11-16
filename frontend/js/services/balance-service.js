const balanceService = {
    async getBalance() {
        return apiClient.call('/balance/');
    },

    async topupBalance(amount) {
        return apiClient.call('/balance/topup', {
            method: 'POST',
            body: JSON.stringify({amount})
        });
    }
};