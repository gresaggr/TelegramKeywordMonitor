const TaskModalComponent = {
    template: `
        <div class="modal-overlay" @mousedown.self="handleOverlayClick" @mouseup.self="handleOverlayRelease">
            <div class="modal-content" style="max-width: 700px; max-height: 90vh; overflow-y: auto;">
                <div class="modal-header">
                    <h2 class="modal-title">{{ isEdit ? 'Edit Monitoring Task' : 'Add Monitoring Task' }}</h2>
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

                <div class="form-group">
                    <label class="form-label">Task Name *</label>
                    <input
                        v-model="form.name"
                        type="text"
                        class="form-input"
                        placeholder="e.g., Биржа, Игры, Новости"
                        required
                    >
                    <small style="color: #718096; font-size: 12px;">Give this monitoring task a descriptive name</small>
                </div>

                <div class="form-group">
                    <label class="form-label">Whitelist Keywords</label>
                    <textarea
                        v-model="whitelistInput"
                        class="form-textarea"
                        placeholder="Enter keywords, one per line (leave empty to accept all messages)"
                        rows="3"
                    ></textarea>
                    <small style="color: #718096; font-size: 12px;">Messages must contain at least one of these words</small>
                </div>

                <div class="form-group">
                    <label class="form-label">Blacklist Keywords</label>
                    <textarea
                        v-model="blacklistInput"
                        class="form-textarea"
                        placeholder="Enter keywords to exclude, one per line"
                        rows="3"
                    ></textarea>
                    <small style="color: #718096; font-size: 12px;">Messages containing these words will be skipped</small>
                </div>

                <div class="form-group">
                    <label class="form-label">Monitored Channels * (max 5)</label>
                    <textarea
                        v-model="channelsInput"
                        class="form-textarea"
                        placeholder="Enter channel IDs or usernames, one per line
Example:
@channelname
-1001234567890"
                        rows="4"
                        required
                    ></textarea>
                    <small style="color: #718096; font-size: 12px;">Channel IDs (numeric) or usernames (@username). Maximum 5 channels.</small>
                </div>

                <div class="form-group">
                    <label class="form-label">Forward To Chat ID *</label>
                    <input
                        v-model="form.forward_to_chat_id"
                        type="text"
                        class="form-input"
                        placeholder="-1001234567890 or @username"
                        required
                    >
                    <small style="color: #718096; font-size: 12px;">Destination channel/chat for forwarded messages</small>
                </div>

                <div class="form-group">
                    <label class="form-label">Text Replacements</label>
                    <textarea
                        v-model="replacementsInput"
                        class="form-textarea"
                        placeholder="Enter replacements in format: old_text -> new_text
Example:
spam -> ⭐️
bad_word -> ***"
                        rows="4"
                    ></textarea>
                    <small style="color: #718096; font-size: 12px;">Replace specific text in messages (one per line: old -> new)</small>
                </div>

                <div class="modal-footer">
                    <button @click="$emit('close')" class="btn btn-secondary" :disabled="loading">
                        Cancel
                    </button>
                    <button @click="handleSave" class="btn btn-primary" :disabled="loading">
                        {{ loading ? 'Saving...' : (isEdit ? 'Save Changes' : 'Create Task') }}
                    </button>
                </div>
            </div>
        </div>
    `,
    props: ['task', 'isEdit', 'accountId', 'user'],
    data() {
        return {
            loading: false,
            error: '',
            overlayClicked: false,
            whitelistInput: '',
            blacklistInput: '',
            channelsInput: '',
            replacementsInput: '',
            form: {
                name: '',
                whitelist_keywords: [],
                blacklist_keywords: [],
                monitored_channels: [],
                forward_to_chat_id: '',
                replacements: {}
            }
        };
    },
    created() {
        this.initializeForm();
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
        initializeForm() {
            if (this.isEdit && this.task) {
                this.form = {
                    name: this.task.name,
                    whitelist_keywords: this.task.whitelist_keywords || [],
                    blacklist_keywords: this.task.blacklist_keywords || [],
                    monitored_channels: this.task.monitored_channels || [],
                    forward_to_chat_id: this.task.forward_to_chat_id || '',
                    replacements: this.task.replacements || {}
                };

                this.whitelistInput = this.form.whitelist_keywords.join('\n');
                this.blacklistInput = this.form.blacklist_keywords.join('\n');
                this.channelsInput = this.form.monitored_channels.join('\n');
                this.replacementsInput = Object.entries(this.form.replacements)
                    .map(([k, v]) => `${k} -> ${v}`).join('\n');
            } else {
                if (this.user) {
                    this.form.forward_to_chat_id = this.user.default_forward_to_chat_id || '';
                }
            }
        },
        parseTextareas() {
            this.form.whitelist_keywords = this.whitelistInput
                .split('\n')
                .map(s => s.trim())
                .filter(s => s.length > 0);

            this.form.blacklist_keywords = this.blacklistInput
                .split('\n')
                .map(s => s.trim())
                .filter(s => s.length > 0);

            this.form.monitored_channels = this.channelsInput
                .split('\n')
                .map(s => s.trim())
                .filter(s => s.length > 0);

            this.form.replacements = {};
            this.replacementsInput.split('\n').forEach(line => {
                const parts = line.split('->').map(s => s.trim());
                if (parts.length === 2 && parts[0] && parts[1]) {
                    this.form.replacements[parts[0]] = parts[1];
                }
            });
        },
        async handleSave() {
            this.error = '';
            this.parseTextareas();

            if (!this.form.name) {
                this.error = 'Please enter a task name';
                return;
            }

            if (this.form.monitored_channels.length === 0) {
                this.error = 'Please add at least one channel to monitor';
                return;
            }

            if (this.form.monitored_channels.length > 5) {
                this.error = 'Maximum number of monitored channels is 5';
                return;
            }

            if (!this.form.forward_to_chat_id) {
                this.error = 'Please specify where to forward messages';
                return;
            }

            this.loading = true;

            try {
                this.$emit('save', this.form);
            } catch (err) {
                this.error = err.message || 'Failed to save task';
            } finally {
                this.loading = false;
            }
        }
    }
};