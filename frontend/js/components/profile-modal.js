// frontend/js/components/profile-modal.js
const ProfileModalComponent = {
    mixins: [modalMixin],
    template: `
        <div class="modal-overlay" @mousedown.self="handleOverlayClick" @mouseup.self="handleOverlayRelease">
            <div class="modal-content" style="max-width: 650px; max-height: 90vh; overflow-y: auto;">
                <div class="modal-header">
                    <h2 class="modal-title">{{ t('modal.profile.title') }}</h2>
                    <button @click="$emit('close')" class="btn-close">
                        <svg viewBox="0 0 24 24">
                            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                        </svg>
                    </button>
                </div>

                <div v-if="error" class="alert alert-error">
                    <svg style="width: 20px; height: 20px; flex-shrink: 0;" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
                    </svg>
                    <span>{{ error }}</span>
                </div>

                <div v-if="success" class="alert alert-success">
                    <svg style="width: 20px; height: 20px; flex-shrink: 0;" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                    </svg>
                    <span>{{ success }}</span>
                </div>

                <h3 style="margin: 20px 0 15px; color: #1a202c;">{{ t('modal.profile.accountInfo') }}</h3>
                
                <div class="form-group">
                    <label class="form-label">{{ t('modal.profile.email') }}</label>
                    <input :value="user.email" type="email" class="form-input" disabled style="background: #f7fafc; cursor: not-allowed;">
                </div>

                <div class="form-group">
                    <label class="form-label">{{ t('modal.profile.username') }}</label>
                    <input :value="user.username" type="text" class="form-input" disabled style="background: #f7fafc; cursor: not-allowed;">
                </div>

                <div class="form-group">
                    <label class="form-label">{{ t('modal.profile.language') }}</label>
                    <select v-model="form.language" class="form-input">
                        <option value="en">{{ t('modal.profile.language.en') }}</option>
                        <option value="ru">{{ t('modal.profile.language.ru') }}</option>
                    </select>
                </div>

                <h3 style="margin: 30px 0 15px; color: #1a202c;">{{ t('modal.profile.telegramSettings') }}</h3>

                <div class="form-group">
                    <label class="form-label">{{ t('modal.profile.chatId') }}</label>
                    <input v-model="form.default_telegram_chat_id" type="text" class="form-input" :placeholder="t('modal.profile.placeholder.chatId')">
                    <small style="color: #718096; font-size: 12px; display: block; margin-top: 5px;">
                        {{ t('modal.profile.hint.chatId') }}
                        <a href="#" @click.prevent="showTelegramHelp = !showTelegramHelp" style="color: #667eea;">{{ t('modal.profile.hint.chatIdHelp') }}</a>
                    </small>
                    <div v-if="showTelegramHelp" class="alert" style="margin-top: 10px; background: #e6f3ff; border: 1px solid #667eea; color: #2c5282;">
                        <div style="font-size: 12px; white-space: pre-line;">{{ t('modal.profile.hint.chatIdSteps') }}</div>
                    </div>
                </div>

                <div class="form-group">
                    <label class="form-label">{{ t('modal.profile.forward') }}</label>
                    <input v-model="form.default_forward_to_chat_id" type="text" class="form-input" :placeholder="t('modal.profile.placeholder.forward')">
                    <small style="color: #718096; font-size: 12px; display: block; margin-top: 5px;">
                        {{ t('modal.profile.hint.forward') }}
                    </small>
                </div>

                <h3 style="margin: 30px 0 15px; color: #1a202c;">{{ t('modal.profile.defaultSettings') }}</h3>
                <p style="color: #718096; font-size: 14px; margin-bottom: 15px;">
                    {{ t('modal.profile.hint.defaults') }}
                </p>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div class="form-group">
                        <label class="form-label">{{ t('modal.profile.apiId') }}</label>
                        <input v-model="form.default_api_id" type="text" class="form-input" :placeholder="t('modal.profile.placeholder.apiId')">
                    </div>
                    <div class="form-group">
                        <label class="form-label">{{ t('modal.profile.apiHash') }}</label>
                        <input v-model="form.default_api_hash" type="text" class="form-input" :placeholder="t('modal.profile.placeholder.apiHash')">
                    </div>
                </div>

                <div class="form-group">
                    <label class="form-label">{{ t('modal.profile.device') }}</label>
                    <input v-model="form.default_device_model" type="text" class="form-input" :placeholder="t('modal.profile.placeholder.device')">
                </div>

                <div class="form-group">
                    <label class="form-label">{{ t('modal.profile.system') }}</label>
                    <input v-model="form.default_system_version" type="text" class="form-input" :placeholder="t('modal.profile.placeholder.system')">
                </div>

                <div class="form-group">
                    <label class="form-label">{{ t('modal.profile.app') }}</label>
                    <input v-model="form.default_app_version" type="text" class="form-input" :placeholder="t('modal.profile.placeholder.app')">
                </div>

                <div class="modal-footer">
                    <button @click="$emit('close')" class="btn btn-secondary" :disabled="loading">{{ t('modal.profile.cancel') }}</button>
                    <button @click="handleSave" class="btn btn-primary" :disabled="loading">
                        {{ loading ? t('modal.profile.saving') : t('modal.profile.save') }}
                    </button>
                </div>
            </div>
        </div>
    `,
    props: ['user'],
    data() {
        return {
            showTelegramHelp: false,
            loading: false,
            error: '',
            success: '',
            form: {
                default_telegram_chat_id: '',
                default_api_id: '',
                default_api_hash: '',
                default_device_model: '',
                default_system_version: '',
                default_app_version: '',
                default_forward_to_chat_id: '',
                language: 'en'
            }
        };
    },
    created() {
        this.initForm();
    },
    watch: {
        user: {
            handler() {
                this.initForm();
            },
            deep: true
        }
    },
    methods: {
        t(key) {
            return window.t ? window.t(key) : key;
        },
        initForm() {
            if (this.user) {
                this.form = {
                    default_telegram_chat_id: this.user.default_telegram_chat_id || '',
                    default_api_id: this.user.default_api_id || '2040',
                    default_api_hash: this.user.default_api_hash || 'b18441a1ff607e10a989891a5462e627',
                    default_device_model: this.user.default_device_model || 'MS-7C75',
                    default_system_version: this.user.default_system_version || 'Windows 10',
                    default_app_version: this.user.default_app_version || '4.8.3',
                    default_forward_to_chat_id: this.user.default_forward_to_chat_id || '',
                    language: this.user.language || 'en'
                };
            }
        },

        async handleSave() {
            this.error = '';
            this.success = '';
            this.loading = true;

            try {
                const data = Object.fromEntries(
                    Object.entries(this.form).map(([k, v]) => [k, v || null])
                );

                await authService.updateProfile(data);
                this.success = this.t('modal.profile.success');

                if (window.setLanguage) {
                    window.setLanguage(this.form.language);
                }

                setTimeout(() => {
                    this.$emit('updated');
                    this.$emit('close');
                }, 1500);
            } catch (err) {
                console.error('Profile update error:', err);
                this.error = err.message || this.t('alert.profileUpdateFailed');
            } finally {
                this.loading = false;
            }
        }
    }
};