// frontend/js/components/account-list-item.js
const AccountListItemComponent = {
    template: `
        <div class="website-item">
            <div class="website-info">
                <div class="website-icon">
                    <svg viewBox="0 0 24 24">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 4c1.93 0 3.5 1.57 3.5 3.5S13.93 13 12 13s-3.5-1.57-3.5-3.5S10.07 6 12 6z"/>
                    </svg>
                </div>
                <div class="website-details">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div class="website-name">{{ account.name ? account.name + ' (' + account.phone_number + ')' : account.phone_number }}</div>
                        <div class="website-actions" style="margin: 0;">
                            <button v-if="account.status === 'awaiting_code' || account.status === 'awaiting_2fa'"
                                    @click="$emit('verify', account)" 
                                    class="btn-icon btn-icon-primary" 
                                    :title="t('account.actions.verify')">
                                <svg viewBox="0 0 24 24" style="fill: #667eea;">
                                    <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-2 16l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z"/>
                                </svg>
                            </button>
                            
                            <button @click="$emit('edit', account)" class="btn-icon" :title="t('account.actions.edit')">
                                <svg viewBox="0 0 24 24">
                                    <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
                                </svg>
                            </button>
                            
                            <button v-if="(account.status === 'active' || account.status === 'stopped') && account.is_active"
                                    @click="$emit('stop', account.id)" 
                                    class="btn-icon" 
                                    :title="t('account.actions.stop')">
                                <svg viewBox="0 0 24 24">
                                    <path d="M6 6h12v12H6z"/>
                                </svg>
                            </button>
                            
                            <button v-else-if="(account.status === 'active' || account.status === 'stopped' || account.status === 'error') && !account.is_active"
                                    @click="$emit('start', account.id)" 
                                    class="btn-icon" 
                                    :title="t('account.actions.start')">
                                <svg viewBox="0 0 24 24">
                                    <path d="M8 5v14l11-7z"/>
                                </svg>
                            </button>
                            
                            <button @click="$emit('delete', account.id)" class="btn-icon btn-icon-danger" :title="t('account.actions.delete')">
                                <svg viewBox="0 0 24 24">
                                    <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                    
                    <div class="website-url" style="display: flex; align-items: center; gap: 10px;">
                        <span class="status-badge" :class="'status-' + account.status">
                            {{ t('account.status.' + account.status) }}
                        </span>
                        <span v-if="account.unread_notifications_count > 0" 
                              class="notification-badge"
                              @click="$emit('show-notifications', account)"
                              title="View notifications">
                            {{ account.unread_notifications_count }} {{ t('notifications.unread') }}
                        </span>
                    </div>
                    
                    <div class="site-info-compact">
                        <div class="site-info-label">{{ t('account.monitoring') }}</div>
                        <div class="site-info-value">
                            <span class="status-badge" :class="account.is_active ? 'status-active' : 'status-stopped'">
                                {{ t(account.is_active ? 'account.status.active' : 'account.status.stopped') }}
                            </span>
                        </div>
                        <div class="site-info-label">{{ t('account.tasks') }}</div>
                        <div class="site-info-value">{{ activeTasksCount }}/{{ account.monitoring_tasks.length }}/5</div>
                        <template v-if="account.last_activity">
                            <div class="site-info-label">{{ t('account.lastActivity') }}</div>
                            <div class="site-info-value">{{ formatDate(account.last_activity) }}</div>
                        </template>
                    </div>

                    <button @click="toggleExpand" class="btn-toggle-details" style="margin-top: 10px;">
                        <span>{{ t(isExpanded ? 'account.details.hide' : 'account.details.show') }}</span>
                        <svg viewBox="0 0 24 24" :class="{ 'rotate-180': isExpanded }">
                            <path d="M7 10l5 5 5-5z"/>
                        </svg>
                    </button>

                    <task-list-component
                        v-if="isExpanded"
                        :account="account"
                        @add-task="$emit('add-task', account)"
                        @edit-task="$emit('edit-task', account, $event)"
                        @start-task="$emit('start-task', account.id, $event)"
                        @stop-task="$emit('stop-task', account.id, $event)"
                        @delete-task="$emit('delete-task', account.id, $event)"
                    ></task-list-component>
                </div>
            </div>
        </div>
    `,
    props: ['account'],
    components: {
        'task-list-component': TaskListComponent
    },
    data() {
        return {
            isExpanded: false
        };
    },
    computed: {
        activeTasksCount() {
            return this.account.monitoring_tasks.filter(t => t.is_active).length;
        }
    },
    methods: {
        t(key) {
            return window.t ? window.t(key) : key;
        },
        toggleExpand() {
            this.isExpanded = !this.isExpanded;
        },
        formatDate(dateString) {
            return uiHelpers.formatDate(dateString);
        }
    }
};