// frontend/js/components/profile-modal.js
const ProfileModalComponent = {
    template: `
        <div class="modal-overlay" @mousedown.self="handleOverlayClick" @mouseup.self="handleOverlayRelease">
            <div class="modal-content" style="max-width: 650px; max-height: 90vh; overflow-y: auto;">
                <div class="modal-header">
                    <h2 class="modal-title">Profile Settings</h2>
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

                <!-- Account Info -->
                <h3 style="margin: 20px 0 15px; color: #1a202c;">Account Information</h3>
                
                <div class="form-group">
                    <label class="form-label">Email (read-only)</label>
                    <input
                        :value="user.email"
                        type="email"
                        class="form-input"
                        disabled
                        style="background: #f7fafc; cursor: not-allowed;"
                    >
                </div>

                <div class="form-group">
                    <label class="form-label">Username (read-only)</label>
                    <input
                        :value="user.username"
                        type="text"
                        class="form-input"
                        disabled
                        style="background: #f7fafc; cursor: not-allowed;"
                    >
                </div>

                <!-- Telegram Settings -->
                <h3 style="margin: 30px 0 15px; color: #1a202c;">Telegram Settings</h3>

                <div class="form-group">
                    <label class="form-label">Default Telegram Chat ID (for error notifications)</label>
                    <input
                        v-model="form.default_telegram_chat_id"
                        type="text"
                        class="form-input"
                        placeholder="123456789 or leave empty"
                    >
                    <small style="color: #718096; font-size: 12px; display: block; margin-top: 5px;">
                        Channel where system error notifications will be sent.
                        <a href="#" @click.prevent="showTelegramHelp = !showTelegramHelp" style="color: #667eea;">
                            How to get Chat ID?
                        </a>
                    </small>
                    <div v-if="showTelegramHelp" class="alert" style="margin-top: 10px; background: #e6f3ff; border: 1px solid #667eea; color: #2c5282;">
                        <div style="font-size: 12px;">
                            <strong>Steps to get your Chat ID:</strong><br>
                            1. Start a chat with @userinfobot in Telegram<br>
                            2. Send any message to the bot<br>
                            3. Copy your Chat ID from the bot's response<br>
                            4. Paste it here
                        </div>
                    </div>
                </div>

                <div class="form-group">
                    <label class="form-label">Default Forward To Chat ID</label>
                    <input
                        v-model="form.default_forward_to_chat_id"
                        type="text"
                        class="form-input"
                        placeholder="-1001234567890 or @username"
                    >
                    <small style="color: #718096; font-size: 12px; display: block; margin-top: 5px;">
                        Default destination for forwarding messages when adding new accounts
                    </small>
                </div>

                <!-- Default Account Settings -->
                <h3 style="margin: 30px 0 15px; color: #1a202c;">Default Telegram Account Settings</h3>
                <p style="color: #718096; font-size: 14px; margin-bottom: 15px;">
                    These values will be used by default when adding new Telegram accounts. You can override them for each account.
                </p>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div class="form-group">
                        <label class="form-label">Default API ID</label>
                        <input
                            v-model="form.default_api_id"
                            type="text"
                            class="form-input"
                            placeholder="2040"
                        >
                    </div>

                    <div class="form-group">
                        <label class="form-label">Default API Hash</label>
                        <input
                            v-model="form.default_api_hash"
                            type="text"
                            class="form-input"
                            placeholder="b18441a1ff607e10a989891a5462e627"
                        >
                    </div>
                </div>

                <div class="form-group">
                    <label class="form-label">Default Device Model</label>
                    <input
                        v-model="form.default_device_model"
                        type="text"
                        class="form-input"
                        placeholder="MS-7C75"
                    >
                </div>

                <div class="form-group">
                    <label class="form-label">Default System Version</label>
                    <input
                        v-model="form.default_system_version"
                        type="text"
                        class="form-input"
                        placeholder="Windows 10"
                    >
                </div>

                <div class="form-group">
                    <label class="form-label">Default App Version</label>
                    <input
                        v-model="form.default_app_version"
                        type="text"
                        class="form-input"
                        placeholder="4.8.3"
                    >
                </div>

                <div class="modal-footer">
                    <button @click="$emit('close')" class="btn btn-secondary" :disabled="loading">
                        Cancel
                    </button>
                    <button @click="handleSave" class="btn btn-primary" :disabled="loading">
                        {{ loading ? 'Saving...' : 'Save Changes' }}
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
            overlayClicked: false,
            form: {
                default_telegram_chat_id: '',
                default_api_id: '',
                default_api_hash: '',
                default_device_model: '',
                default_system_version: '',
                default_app_version: '',
                default_forward_to_chat_id: ''
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
            deep: true,
            immediate: true
        }
    },
    methods: {
        initForm() {
            if (this.user) {
                this.form = {
                    default_telegram_chat_id: this.user.default_telegram_chat_id || '',
                    default_api_id: this.user.default_api_id || '2040',
                    default_api_hash: this.user.default_api_hash || 'b18441a1ff607e10a9895462e627',
                    default_device_model: this.user.default_device_model || 'MS-7C75',
                    default_system_version: this.user.default_system_version || 'Windows 10',
                    default_app_version: this.user.default_app_version || '4.8.3',
                    default_forward_to_chat_id: this.user.default_forward_to_chat_id || ''
                };
            }
        },
        handleOverlayClick() {
            this.overlayClicked = true;
        },
        handleOverlayRelease() {
            if (this.overlayClicked) {
                this.$emit('close');
            }
            this.overlayClicked = false;
        },
        async handleSave() {
            this.error = '';
            this.success = '';
            this.loading = true;

            try {
                const data = {
                    default_telegram_chat_id: this.form.default_telegram_chat_id || null,
                    default_api_id: this.form.default_api_id || null,
                    default_api_hash: this.form.default_api_hash || null,
                    default_device_model: this.form.default_device_model || null,
                    default_system_version: this.form.default_system_version || null,
                    default_app_version: this.form.default_app_version || null,
                    default_forward_to_chat_id: this.form.default_forward_to_chat_id || null
                };

                await api.updateProfile(data);
                this.success = 'Profile updated successfully!';

                setTimeout(() => {
                    this.$emit('updated');
                    this.$emit('close');
                }, 1500);
            } catch (err) {
                console.error('Profile update error:', err);
                this.error = err.message || 'Failed to update profile';
            } finally {
                this.loading = false;
            }
        }
    }
};