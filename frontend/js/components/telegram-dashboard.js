// frontend/js/components/telegram-dashboard.js
const TelegramDashboardComponent = {
    name: 'TelegramDashboardComponent',
    components: {
        'account-modal-component': AccountModalComponent,
        'verify-code-modal-component': VerifyCodeModalComponent,
        'profile-modal-component': ProfileModalComponent
    },
    template: `
        <div class="dashboard">
            <div class="header">
                <div class="header-content">
                    <div class="header-brand">
                        <div class="header-icon">
                            <svg viewBox="0 0 24 24">
                                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z"/>
                            </svg>
                        </div>
                        <div class="header-text">
                            <h1>Telegram Monitor</h1>
                            <p>Dashboard</p>
                        </div>
                    </div>
                    <div class="header-user">
                        <div class="user-info">
                            <div class="user-name">{{ user.username }}</div>
                            <div class="user-email">{{ user.email }}</div>
                            <div class="user-balance">Balance: {{user.balance.toFixed(2)}}</div>
                        </div>
                        <button @click="showProfileModal = true" class="btn-settings" title="Profile Settings">
                            <svg viewBox="0 0 24 24" style="width: 20px; height: 20px; fill: currentColor;">
                                <path d="M19.14,12.94c0.04-0.3,0.06-0.61,0.06-0.94c0-0.32-0.02-0.64-0.07-0.94l2.03-1.58c0.18-0.14,0.23-0.41,0.12-0.61 l-1.92-3.32c-0.12-0.22-0.37-0.29-0.59-0.22l-2.39,0.96c-0.5-0.38-1.03-0.7-1.62-0.94L14.4,2.81c-0.04-0.24-0.24-0.41-0.48-0.41 h-3.84c-0.24,0-0.43,0.17-0.47,0.41L9.25,5.35C8.66,5.59,8.12,5.92,7.63,6.29L5.24,5.33c-0.22-0.08-0.47,0-0.59,0.22L2.74,8.87 C2.62,9.08,2.66,9.34,2.86,9.48l2.03,1.58C4.84,11.36,4.8,11.69,4.8,12s0.02,0.64,0.07,0.94l-2.03,1.58 c-0.18,0.14-0.23,0.41-0.12,0.61l1.92,3.32c0.12,0.22,0.37,0.29,0.59,0.22l2.39-0.96c0.5,0.38,1.03,0.7,1.62,0.94l0.36,2.54 c0.05,0.24,0.24,0.41,0.48,0.41h3.84c0.24,0,0.44-0.17,0.47-0.41l0.36-2.54c0.59-0.24,1.13-0.56,1.62-0.94l2.39,0.96 c0.22,0.08,0.47,0,0.59-0.22l1.92-3.32c0.12-0.22,0.07-0.47-0.12-0.61L19.14,12.94z M12,15.6c-1.98,0-3.6-1.62-3.6-3.6 s1.62-3.6,3.6-3.6s3.6,1.62,3.6,3.6S13.98,15.6,12,15.6z"/>
                            </svg>
                        </button>
                        <button @click="showTopupModal = true" class="btn-settings" title="Top Up Balance">
                            <svg viewBox="0 0 24 24" style="width: 20px; height: 20px; fill: currentColor;">
                                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm5 11h-4v4h-2v-4H7v-2h4V7h2v4h4v2z"/>
                            </svg>
                        </button>
                        <button @click="$emit('logout')" class="btn-logout">Logout</button>
                    </div>
                </div>
            </div>

            <div class="container">
                <!-- Stats -->
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-header">
                            <div>
                                <div class="stat-label">Total Accounts</div>
                                <div class="stat-value">{{ accounts.length }}</div>
                            </div>
                            <div class="stat-icon" style="background: #bee3f8;">
                                <svg viewBox="0 0 24 24" fill="#2c5282">
                                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 4c1.93 0 3.5 1.57 3.5 3.5S13.93 13 12 13s-3.5-1.57-3.5-3.5S10.07 6 12 6z"/>
                                </svg>
                            </div>
                        </div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-header">
                            <div>
                                <div class="stat-label">Active</div>
                                <div class="stat-value">{{ activeCount }}</div>
                            </div>
                            <div class="stat-icon" style="background: #c6f6d5;">
                                <svg viewBox="0 0 24 24" fill="#2f855a">
                                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                                </svg>
                            </div>
                        </div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-header">
                            <div>
                                <div class="stat-label">Issues</div>
                                <div class="stat-value">{{ errorCount }}</div>
                            </div>
                            <div class="stat-icon" style="background: #fed7d7;">
                                <svg viewBox="0 0 24 24" fill="#c53030">
                                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
                                </svg>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Account List -->
                <div class="website-header">
                    <h2 class="website-title">Telegram Accounts ({{ accounts.length }}/5)</h2>
                    <button @click="handleAddClick" class="btn btn-primary btn-add-website">
                        <svg viewBox="0 0 24 24" style="width: 20px; height: 20px; fill: currentColor; margin-right: 8px;">
                            <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
                        </svg>
                        Add Account
                    </button>
                </div>

                <div v-if="accounts.length === 0" class="empty-state">
                    <div class="empty-icon">
                        <svg viewBox="0 0 24 24">
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 4c1.93 0 3.5 1.57 3.5 3.5S13.93 13 12 13s-3.5-1.57-3.5-3.5S10.07 6 12 6z"/>
                        </svg>
                    </div>
                    <h3>No accounts yet</h3>
                    <p>Add your first Telegram account to start monitoring channels</p>
                    <button @click="handleAddClick" class="btn btn-primary" style="width: auto; padding: 12px 32px;">
                        Add Your First Account
                    </button>
                </div>

                <div v-else class="website-list">
                    <div v-for="account in accounts" :key="account.id" class="website-item">
                        <div class="website-info">
                            <div class="website-icon">
                                <svg viewBox="0 0 24 24">
                                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 4c1.93 0 3.5 1.57 3.5 3.5S13.93 13 12 13s-3.5-1.57-3.5-3.5S10.07 6 12 6z"/>
                                </svg>
                            </div>
                            <div class="website-details">
                                <div class="website-name">{{ account.phone_number }}</div>
                                <div class="website-url" style="display: flex; align-items: center; gap: 10px;">
                                    <span class="status-badge" :class="'status-' + account.status">
                                        {{ account.status }}
                                    </span>
                                    <span v-if="account.unread_notifications_count > 0" 
                                          class="notification-badge"
                                          @click="showNotifications(account)"
                                          title="View notifications">
                                        {{ account.unread_notifications_count }} unread
                                    </span>
                                </div>
                                
                                <!-- Compact info -->
                                <div class="site-info-compact">
                                    <div class="site-info-label">Monitoring:</div>
                                    <div class="site-info-value">
                                        <span class="status-badge" :class="account.is_active ? 'status-active' : 'status-stopped'">
                                            {{ account.is_active ? 'Active' : 'Stopped' }}
                                        </span>
                                    </div>
                                </div>

                                <!-- Detailed info -->
                                <div v-if="expandedItems[account.id]" class="site-info-grid">
                                    <div class="site-info-label">Channels:</div>
                                    <div class="site-info-value">
                                        {{ account.monitored_channels.length }} ({{ account.monitored_channels.join(', ') }})
                                    </div>

                                    <div class="site-info-label">Whitelist:</div>
                                    <div class="site-info-value">
                                        <template v-if="account.whitelist_keywords.length > 0">
                                            {{ account.whitelist_keywords.length }} ({{ account.whitelist_keywords.join(', ') }})
                                        </template>
                                        <template v-else>All messages</template>
                                    </div>

                                    <div class="site-info-label">Blacklist:</div>
                                    <div class="site-info-value">
                                        <template v-if="account.blacklist_keywords.length > 0">
                                            {{ account.blacklist_keywords.length }} ({{ account.blacklist_keywords.join(', ') }})
                                        </template>
                                        <template v-else>None</template>
                                    </div>

                                    <div class="site-info-label">Forward to:</div>
                                    <div class="site-info-value">{{ account.forward_to_chat_id || 'Not set' }}</div>

                                    <div class="site-info-label">Replacements:</div>
                                    <div class="site-info-value">
                                        {{ Object.keys(account.replacements).length }} rules
                                    </div>

                                    <template v-if="account.last_activity">
                                        <div class="site-info-label">Last activity:</div>
                                        <div class="site-info-value">{{ formatDate(account.last_activity) }}</div>
                                    </template>

                                    <template v-if="account.error_message">
                                        <div class="site-info-label">Error:</div>
                                        <div class="site-info-value" style="color: #e53e3e;">{{ account.error_message }}</div>
                                    </template>
                                </div>

                                <button @click="toggleExpand(account.id)" class="btn-toggle-details">
                                    <span>{{ expandedItems[account.id] ? 'Hide details' : 'Show details' }}</span>
                                    <svg viewBox="0 0 24 24" :class="{ 'rotate-180': expandedItems[account.id] }">
                                        <path d="M7 10l5 5 5-5z"/>
                                    </svg>
                                </button>
                            </div>
                        </div>
                        
                        <div class="website-actions">
                            <!-- Show Verify button if waiting for code -->
                            <button v-if="account.status === 'awaiting_code' || account.status === 'awaiting_2fa'"
                                    @click="showVerifyModal(account)" 
                                    class="btn-icon btn-icon-primary" 
                                    title="Verify Code">
                                <svg viewBox="0 0 24 24" style="fill: #667eea;">
                                    <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-2 16l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z"/>
                                </svg>
                            </button>
                            
                            <!-- Start/Stop -->
                            <button v-if="account.status === 'active' && account.is_active"
                                    @click="handleStop(account.id)" 
                                    class="btn-icon" 
                                    title="Stop">
                                <svg viewBox="0 0 24 24">
                                    <path d="M6 6h12v12H6z"/>
                                </svg>
                            </button>
                            
                            <button v-else-if="(account.status === 'active' || account.status === 'stopped') && !account.is_active"
                                    @click="handleStart(account.id)" 
                                    class="btn-icon" 
                                    title="Start">
                                <svg viewBox="0 0 24 24">
                                    <path d="M8 5v14l11-7z"/>
                                </svg>
                            </button>
                            
                            <button @click="handleEdit(account)" class="btn-icon" title="Edit">
                                <svg viewBox="0 0 24 24">
                                    <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
                                </svg>
                            </button>
                            
                            <button @click="handleDelete(account.id)" class="btn-icon btn-icon-danger" title="Delete">
                                <svg viewBox="0 0 24 24">
                                    <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Modals -->
                <account-modal-component
                    v-if="showAddModal || showEditModal"
                    :account="editingAccount"
                    :is-edit="showEditModal"
                    :user="user"
                    @close="closeModals"
                    @save="handleSave"
                ></account-modal-component>

                <verify-code-modal-component
                    v-if="showVerifyCodeModal"
                    :account="verifyingAccount"
                    @close="showVerifyCodeModal = false"
                    @verified="handleVerified"
                ></verify-code-modal-component>

                <profile-modal-component
                    v-if="showProfileModal"
                    :user="user"
                    @close="showProfileModal = false"
                    @updated="handleProfileUpdated"
                ></profile-modal-component>

                <!-- Topup Modal -->
                <div v-if="showTopupModal" class="modal-overlay" @click.self="showTopupModal = false">
                    <div class="modal-content" style="max-width: 400px;">
                        <div class="modal-header">
                            <h2 class="modal-title">Top Up Balance</h2>
                            <button @click="showTopupModal = false" class="btn-close">
                                <svg viewBox="0 0 24 24">
                                    <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                                </svg>
                            </button>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Amount ($)</label>
                            <input v-model.number="topupAmount" type="number" class="form-input" placeholder="10.00" min="1" step="0.01">
                        </div>
                        <div class="modal-footer">
                            <button @click="showTopupModal = false" class="btn btn-secondary">Cancel</button>
                            <button @click="handleTopup" class="btn btn-primary">Add Funds (Stub)</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `,
    props: ['user', 'accounts'],
    data() {
        return {
            showAddModal: false,
            showEditModal: false,
            showVerifyCodeModal: false,
            showTopupModal: false,
            showProfileModal: false,
            editingAccount: null,
            verifyingAccount: null,
            expandedItems: {},
            topupAmount: 10
        };
    },
    computed: {
        activeCount() {
            return this.accounts.filter(a => a.is_active && a.status === 'active').length;
        },
        errorCount() {
            return this.accounts.filter(a => a.status === 'error' || a.unread_notifications_count > 0).length;
        }
    },
    methods: {
        handleAddClick() {
            if (this.accounts.length >= 5) {
                alert('Maximum number of accounts (5) reached. Please delete an existing account to add a new one.');
                return;
            }
            this.showAddModal = true;
        },

        toggleExpand(accountId) {
            this.expandedItems[accountId] = !this.expandedItems[accountId];
        },

        formatDate(dateString) {
            const date = new Date(dateString);
            const now = new Date();
            const diff = now - date;

            if (diff < 60000) return 'Just now';
            if (diff < 3600000) {
                const minutes = Math.floor(diff / 60000);
                return `${minutes}m ago`;
            }
            if (diff < 86400000) {
                const hours = Math.floor(diff / 3600000);
                return `${hours}h ago`;
            }
            return date.toLocaleString();
        },

        handleEdit(account) {
            this.editingAccount = {...account};
            this.showEditModal = true;
        },

        showVerifyModal(account) {
            this.verifyingAccount = account;
            this.showVerifyCodeModal = true;
        },

        async handleDelete(accountId) {
            if (confirm('Are you sure you want to delete this account? This will stop monitoring and delete the session.')) {
                this.$emit('delete-account', accountId);
            }
        },

        async handleStart(accountId) {
            this.$emit('start-account', accountId);
        },

        async handleStop(accountId) {
            if (confirm('Stop monitoring this account?')) {
                this.$emit('stop-account', accountId);
            }
        },

        closeModals() {
            this.showAddModal = false;
            this.showEditModal = false;
            this.editingAccount = null;
        },

        handleSave(data) {
            if (this.showEditModal) {
                this.$emit('edit-account', this.editingAccount.id, data);
            } else {
                this.$emit('add-account', data);
            }
            this.closeModals();
        },

        handleVerified() {
            this.showVerifyCodeModal = false;
            this.$emit('reload-accounts');
        },

        async showNotifications(account) {
            try {
                const notifications = await api.getAccountNotifications(account.id);
                const messages = notifications.map(n =>
                    `[${new Date(n.created_at).toLocaleString()}] ${n.message}`
                ).join('\n\n');

                alert(`Notifications for ${account.phone_number}:\n\n${messages || 'No notifications'}`);

                for (const n of notifications) {
                    if (!n.is_read) {
                        await api.markNotificationRead(account.id, n.id);
                    }
                }

                this.$emit('reload-accounts');
            } catch (err) {
                alert('Failed to load notifications: ' + err.message);
            }
        },

        async handleTopup() {
            try {
                await api.topupBalance(this.topupAmount);
                this.showTopupModal = false;
                this.$emit('reload-user');
                alert('Balance topped up! (This is a stub - real payment integration needed)');
            } catch (err) {
                alert('Failed to top up: ' + err.message);
            }
        },

        handleProfileUpdated() {
            this.$emit('reload-user');
        }
    }
};