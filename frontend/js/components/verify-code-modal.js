const VerifyCodeModalComponent = {
    template: `
        <div class="modal-overlay" @mousedown.self="handleOverlayClick" @mouseup.self="handleOverlayRelease">
            <div class="modal-content" style="max-width: 450px;">
                <div class="modal-header">
                    <h2 class="modal-title">Verify Code</h2>
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

                <p style="color: #718096; margin-bottom: 20px;">
                    Enter the verification code sent to your phone: <strong>{{ account.phone_number }}</strong>
                </p>

                <div class="form-group">
                    <label class="form-label">Verification Code *</label>
                    <input
                        v-model="code"
                        type="text"
                        class="form-input"
                        placeholder="12345"
                        @keyup.enter="handleVerify"
                        required
                        autofocus
                    >
                </div>

                <div v-if="needs2FA" class="form-group">
                    <label class="form-label">Two-Factor Password</label>
                    <input
                        v-model="twoFaPassword"
                        type="password"
                        class="form-input"
                        placeholder="Enter 2FA password"
                        @keyup.enter="handleVerify"
                    >
                    <small style="color: #718096; font-size: 12px;">
                        Your account has 2FA enabled. Please enter your password.
                    </small>
                </div>

                <div class="modal-footer">
                    <button @click="$emit('close')" class="btn btn-secondary" :disabled="loading">
                        Cancel
                    </button>
                    <button @click="handleVerify" class="btn btn-primary" :disabled="loading || !code">
                        {{ loading ? 'Verifying...' : 'Verify' }}
                    </button>
                </div>
            </div>
        </div>
    `,
    props: ['account'],
    data() {
        return {
            loading: false,
            error: '',
            success: '',
            needs2FA: false,
            overlayClicked: false,
            code: '',
            twoFaPassword: ''
        };
    },
    methods: {
        handleOverlayClick() {
            this.overlayClicked = true;
        },
        handleOverlayRelease() {
            if (this.overlayClicked) {
                this.$emit('close');
            }
            this.overlayClicked = false;
        },
        async handleVerify() {
            if (!this.code) {
                this.error = 'Please enter the verification code';
                return;
            }

            this.error = '';
            this.success = '';
            this.loading = true;

            try {
                await api.verifyCode(
                    this.account.id,
                    this.code,
                    this.twoFaPassword || null
                );

                this.success = 'Account verified successfully!';

                setTimeout(() => {
                    this.$emit('verified');
                }, 1500);

            } catch (err) {
                this.error = err.message || 'Verification failed';

                // Check if 2FA is needed
                if (this.error.includes('2FA') || this.error.includes('password required')) {
                    this.needs2FA = true;
                }
            } finally {
                this.loading = false;
            }
        }
    }
};