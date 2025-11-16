// frontend/js/components/topup-modal.js
const TopupModalComponent = {
    mixins: [modalMixin],
    template: `
        <div class="modal-overlay" @mousedown.self="handleOverlayClick" @mouseup.self="handleOverlayRelease">
            <div class="modal-content" style="max-width: 400px;">
                <div class="modal-header">
                    <h2 class="modal-title">Top Up Balance</h2>
                    <button @click="$emit('close')" class="btn-close">
                        <svg viewBox="0 0 24 24">
                            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                        </svg>
                    </button>
                </div>
                <div class="form-group">
                    <label class="form-label">Amount ($)</label>
                    <input v-model.number="amount" type="number" class="form-input" placeholder="10.00" min="1" step="0.01">
                </div>
                <div class="modal-footer">
                    <button @click="$emit('close')" class="btn btn-secondary">Cancel</button>
                    <button @click="handleTopup" class="btn btn-primary">Add Funds (Stub)</button>
                </div>
            </div>
        </div>
    `,
    data() {
        return {
            amount: 10
        };
    },
    methods: {
        async handleTopup() {
            try {
                await balanceService.topupBalance(this.amount);
                this.$emit('topup-success');
                this.$emit('close');
            } catch (err) {
                alert('Failed to top up: ' + err.message);
            }
        }
    }
};