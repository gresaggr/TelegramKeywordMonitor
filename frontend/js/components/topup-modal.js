// frontend/js/components/topup-modal.js
const TopupModalComponent = {
    mixins: [modalMixin],
    template: `
        <div class="modal-overlay" @mousedown.self="handleOverlayClick" @mouseup.self="handleOverlayRelease">
            <div class="modal-content" style="max-width: 450px;">
                <div class="modal-header">
                    <h2 class="modal-title">{{ t('modal.topup.title') }}</h2>
                    <button @click="$emit('close')" class="btn-close">
                        <svg viewBox="0 0 24 24">
                            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                        </svg>
                    </button>
                </div>

                <div v-if="error" class="alert alert-error">
                    <svg style="width: 20px; height: 20px;" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
                    </svg>
                    <span>{{ error }}</span>
                </div>

                <div v-if="success" class="alert alert-success">
                    <svg style="width: 20px; height: 20px;" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                    </svg>
                    <span>{{ success }}</span>
                </div>

                <div class="form-group">
                    <label class="form-label">{{ t('modal.topup.amount') }}</label>
                    <input 
                        v-model.number="amount" 
                        type="number" 
                        class="form-input" 
                        placeholder="100.00" 
                        min="1" 
                        step="0.01"
                        :disabled="loading"
                    >
                    <small style="color: #718096; font-size: 12px; display: block; margin-top: 5px;">
                        {{ t('modal.topup.hint') }}
                    </small>
                </div>

                <div style="background: #f7fafc; padding: 12px; border-radius: 8px; margin: 15px 0;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="color: #718096;">{{ t('modal.topup.paymentMethod') }}:</span>
                        <span style="font-weight: 600;">💳 YooKassa</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #718096;">{{ t('modal.topup.total') }}:</span>
                        <span style="font-weight: 600; color: #667eea;">{{ amount }} RUB</span>
                    </div>
                </div>

                <div class="modal-footer">
                    <button @click="$emit('close')" class="btn btn-secondary" :disabled="loading">
                        {{ t('modal.topup.cancel') }}
                    </button>
                    <button @click="handleTopup" class="btn btn-primary" :disabled="loading || amount < 1">
                        {{ loading ? t('modal.topup.processing') : t('modal.topup.pay') }}
                    </button>
                </div>
            </div>
        </div>
    `,
    data() {
        return {
            amount: 100,
            loading: false,
            error: '',
            success: ''
        };
    },
    methods: {
        t(key) {
            return window.t ? window.t(key) : key;
        },
        async handleTopup() {
            if (this.amount < 1) {
                this.error = this.t('modal.topup.error.minAmount');
                return;
            }

            this.error = '';
            this.success = '';
            this.loading = true;

            try {
                // Create payment via API
                const payment = await apiClient.call('/payments/create', {
                    method: 'POST',
                    body: JSON.stringify({
                        amount: this.amount,
                        description: `Balance top-up: ${this.amount} RUB`
                    })
                });

                if (payment.confirmation_url) {
                    // Redirect to YooKassa payment page
                    window.location.href = payment.confirmation_url;
                } else {
                    throw new Error('No confirmation URL received');
                }
            } catch (err) {
                console.error('Payment error:', err);
                this.error = err.message || this.t('alert.topupFailed');
                this.loading = false;
            }
        }
    }
};