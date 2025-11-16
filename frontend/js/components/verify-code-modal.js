// frontend/js/components/verify-code-modal.js
const VerifyCodeModalComponent = {
    mixins: [modalMixin],
    template: `
        <div class="modal-overlay" @mousedown.self="handleOverlayClick" @mouseup.self="handleOverlayRelease">
            <div class="modal-content" style="max-width: 450px;">
                <div class="modal-header">
                    <h2 class="modal-title">{{ t('modal.verify.title') }}</h2>
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
                    {{ t('modal.verify.desc') }} <strong>{{ account.phone_number }}</strong>
                </p>

                <div class="form-group">
                    <label class="form-label">{{ t('modal.verify.code') }}</label>
                    <input v-model="code" type="text" class="form-input" :placeholder="t('modal.verify.placeholder.code')" @keyup.enter="handleVerify" required autofocus>
                </div>

                <div v-if="needs2FA" class="form-group">
                    <label class="form-label">{{ t('modal.verify.2fa') }}</label>
                    <div class="password-input-wrapper">
                        <input v-model="twoFaPassword" :type="showPassword ? 'text' : 'password'" class="form-input" 
                               :placeholder="t('modal.verify.placeholder.2fa')" @keyup.enter="handleVerify">
                        <button @click="showPassword = !showPassword" class="password-toggle" type="button">
                            <svg v-if="!showPassword" viewBox="0 0 24 24" width="20" height="20">
                                <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
                            </svg>
                            <svg v-else viewBox="0 0 24 24" width="20" height="20">
                                <path d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z"/>
                            </svg>
                        </button>
                    </div>
                    <small style="color: #718096; font-size: 12px;">{{ t('modal.verify.2fa.desc') }}</small>
                </div>

                <div class="modal-footer">
                    <button @click="$emit('close')" class="btn btn-secondary" :disabled="loading">{{ t('modal.verify.cancel') }}</button>
                    <button @click="handleVerify" class="btn btn-primary" :disabled="loading || !code">
                        {{ loading ? t('modal.verify.verifying') : t('modal.verify.verify') }}
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
            code: '',
            twoFaPassword: '',
            showPassword: false
        };
    },
    methods: {
        t(key) {
            return window.t ? window.t(key) : key;
        },
        async handleVerify() {
            if (!this.code) {
                this.error = this.t('modal.verify.error.code');
                return;
            }

            this.error = '';
            this.success = '';
            this.loading = true;

            try {
                await accountService.verifyCode(this.account.id, this.code, this.twoFaPassword || null);
                this.success = this.t('modal.verify.success');
                setTimeout(() => this.$emit('verified'), 1500);
            } catch (err) {
                this.error = err.message || this.t('alert.verificationFailed');
                if (this.error.includes('2FA') || this.error.includes('password required')) {
                    this.needs2FA = true;
                }
            } finally {
                this.loading = false;
            }
        }
    }
};