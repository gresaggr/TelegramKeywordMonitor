const AccountModalComponent = {
    template: `
        <div class="modal-overlay" @mousedown.self="handleOverlayClick" @mouseup.self="handleOverlayRelease">
            <div class="modal-content" style="max-width: 700px; max-height: 90vh; overflow-y: auto;">
                <div class="modal-header">
                    <h2 class="modal-title">Add Telegram Account</h2>
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
                <h3 style="margin: 20px 0 15px; color: #1a202c;">Authentication</h3>
                <div class="form-group">
                <label class="form-label">Phone Number *</label>
                <input
                    v-model="form.phone_number"
                    type="tel"
                    class="form-input"
                    placeholder="+1234567890"
                    required
                >
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                <div class="form-group">
                    <label class="form-label">API ID *</label>
                    <input
                        v-model="form.api_id"
                        type="text"
                        class="form-input"
                        placeholder="12345678"
                        required
                    >
                </div>

                <div class="form-group">
                    <label class="form-label">API Hash *</label>
                    <input
                        v-model="form.api_hash"
                        type="text"
                        class="form-input"
                        placeholder="abcdef123456..."
                        required
                    >
                </div>
            </div>

            <small style="color: #718096; font-size: 12px; display: block; margin: 10px 0;">
                Get your API credentials from <a href="https://my.telegram.org" target="_blank" style="color: #667eea;">my.telegram.org</a>
            </small>

            <details style="margin: 15px 0;">
                <summary style="cursor: pointer; color: #667eea; font-weight: 600;">Device Settings</summary>
                <div style="padding: 15px 0;">
                    <div class="form-group">
                        <label class="form-label">Device Model</label>
                        <input v-model="form.device_model" type="text" class="form-input" placeholder="MS-7C75">
                    </div>
                    <div class="form-group">
                        <label class="form-label">System Version</label>
                        <input v-model="form.system_version" type="text" class="form-input" placeholder="Windows 10">
                    </div>
                    <div class="form-group">
                        <label class="form-label">App Version</label>
                        <input v-model="form.app_version" type="text" class="form-input" placeholder="4.8.3">
                    </div>
                </div>
            </details>

            <details style="margin: 15px 0;">
                <summary style="cursor: pointer; color: #667eea; font-weight: 600;">Proxy Settings (Optional)</summary>
                <div style="padding: 15px 0;">
                    <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 15px;">
                        <div class="form-group">
                            <label class="form-label">Proxy Host</label>
                            <input v-model="form.proxy.host" type="text" class="form-input" placeholder="proxy.example.com">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Port</label>
                            <input v-model.number="form.proxy.port" type="number" class="form-input" placeholder="1080">
                        </div>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                        <div class="form-group">
                            <label class="form-label">Username</label>
                            <input v-model="form.proxy.username" type="text" class="form-input">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Password</label>
                            <input v-model="form.proxy.password" type="password" class="form-input">
                        </div>
                    </div>
                </div>
            </details>

            <div class="modal-footer">
                <button @click="$emit('close')" class="btn btn-secondary" :disabled="loading">
                    Cancel
                </button>
                <button @click="handleSave" class="btn btn-primary" :disabled="loading">
                    {{ loading ? 'Creating...' : 'Create Account' }}
                </button>
            </div>
        </div>
    </div>
`,
    props: ['user'],
    data() {
        return {
            loading: false,
            error: '',
            overlayClicked: false,
            form: {
                phone_number: '',
                api_id: '',
                api_hash: '',
                device_model: 'MS-7C75',
                system_version: 'Windows 10',
                app_version: '4.8.3',
                proxy: {
                    host: '',
                    port: null,
                    username: '',
                    password: ''
                }
            }
        };
    },
    created() {
        if (this.user) {
            this.form.api_id = this.user.default_api_id || '2040';
            this.form.api_hash = this.user.default_api_hash || 'b18441a1ff607e10a989891a5462e627';
            this.form.device_model = this.user.default_device_model || 'MS-7C75';
            this.form.system_version = this.user.default_system_version || 'Windows 10';
            this.form.app_version = this.user.default_app_version || '4.8.3';
        }
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
        async handleSave() {
            this.error = '';

            if (!this.form.phone_number || !this.form.api_id || !this.form.api_hash) {
                this.error = 'Please fill in phone number, API ID and API Hash';
                return;
            }

            this.loading = true;

            try {
                const data = {...this.form};

                if (!data.proxy || !data.proxy.host) {
                    delete data.proxy;
                }

                this.$emit('save', data);
            } catch (err) {
                this.error = err.message || 'Failed to save account';
            } finally {
                this.loading = false;
            }
        }
    }
};