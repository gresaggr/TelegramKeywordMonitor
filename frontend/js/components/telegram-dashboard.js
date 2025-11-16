// frontend/js/components/telegram-dashboard.js
const TelegramDashboardComponent = {
    components: {
        'dashboard-header-component': DashboardHeaderComponent,
        'stats-section-component': StatsSectionComponent,
        'account-list-item-component': AccountListItemComponent,
        'task-list-component': TaskListComponent,
        'task-item-component': TaskItemComponent,
        'account-modal-component': AccountModalComponent,
        'task-modal-component': TaskModalComponent,
        'verify-code-modal-component': VerifyCodeModalComponent,
        'profile-modal-component': ProfileModalComponent,
        'topup-modal-component': TopupModalComponent
    },
    template: `
        <div class="dashboard">
            <dashboard-header-component
                :user="user"
                @logout="$emit('logout')"
                @open-profile="showProfileModal = true"
                @open-topup="showTopupModal = true"
            ></dashboard-header-component>

            <div class="container">
                <stats-section-component
                    :total-accounts="accounts.length"
                    :total-tasks="totalTasks"
                    :error-count="errorCount"
                ></stats-section-component>

                <div class="website-header">
                    <h2 class="website-title">{{ t('accounts.title') }} ({{ accounts.length }}/5)</h2>
                    <button @click="handleAddAccountClick" class="btn btn-primary btn-add-website">
                        <svg viewBox="0 0 24 24" style="width: 20px; height: 20px; fill: currentColor; margin-right: 8px;">
                            <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
                        </svg>
                        {{ t('accounts.add') }}
                    </button>
                </div>

                <div v-if="accounts.length === 0" class="empty-state">
                    <div class="empty-icon">
                        <svg viewBox="0 0 24 24">
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 4c1.93 0 3.5 1.57 3.5 3.5S13.93 13 12 13s-3.5-1.57-3.5-3.5S10.07 6 12 6z"/>
                        </svg>
                    </div>
                    <h3>{{ t('accounts.empty.title') }}</h3>
                    <p>{{ t('accounts.empty.desc') }}</p>
                    <button @click="handleAddAccountClick" class="btn btn-primary" style="width: auto; padding: 12px 32px;">
                        {{ t('accounts.empty.button') }}
                    </button>
                </div>

                <div v-else class="website-list">
                    <account-list-item-component
                        v-for="account in accounts"
                        :key="account.id"
                        :account="account"
                        @verify="showVerifyModal"
                        @edit="handleEditAccount"
                        @start="handleStart"
                        @stop="handleStop"
                        @delete="handleDelete"
                        @show-notifications="showNotifications"
                        @add-task="handleAddTask"
                        @edit-task="handleEditTask"
                        @start-task="handleStartTask"
                        @stop-task="handleStopTask"
                        @delete-task="handleDeleteTask"
                    ></account-list-item-component>
                </div>

                <account-modal-component
                    v-if="showAddAccountModal"
                    :user="user"
                    :account="editingAccount"
                    :is-edit="isEditingAccount"
                    @close="closeAccountModal"
                    @save="handleSaveAccount"
                ></account-modal-component>

                <task-modal-component
                    v-if="showTaskModal"
                    :task="editingTask"
                    :is-edit="isEditingTask"
                    :account-id="currentAccountId"
                    :user="user"
                    @close="closeTaskModal"
                    @save="handleSaveTask"
                ></task-modal-component>

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
                    @updated="$emit('reload-user')"
                ></profile-modal-component>

                <topup-modal-component
                    v-if="showTopupModal"
                    @close="showTopupModal = false"
                    @topup-success="handleTopupSuccess"
                ></topup-modal-component>
            </div>
        </div>
    `,
    props: ['user', 'accounts'],
    data() {
        return {
            showAddAccountModal: false,
            showTaskModal: false,
            showVerifyCodeModal: false,
            showTopupModal: false,
            showProfileModal: false,
            verifyingAccount: null,
            editingTask: null,
            isEditingTask: false,
            currentAccountId: null,
            editingAccount: null,
            isEditingAccount: false
        };
    },
    computed: {
        totalTasks() {
            return this.accounts.reduce((sum, acc) => sum + acc.monitoring_tasks.length, 0);
        },
        errorCount() {
            return this.accounts.filter(a => a.status === 'error' || a.unread_notifications_count > 0).length;
        }
    },
    methods: {
        t(key) {
            return window.t ? window.t(key) : key;
        },
        handleAddAccountClick() {
            if (this.accounts.length >= 5) {
                alert(this.t('error.max.accounts'));
                return;
            }
            this.editingAccount = null;
            this.isEditingAccount = false;
            this.showAddAccountModal = true;
        },

        handleEditAccount(account) {
            this.editingAccount = account;
            this.isEditingAccount = true;
            this.showAddAccountModal = true;
        },

        closeAccountModal() {
            this.showAddAccountModal = false;
            this.editingAccount = null;
            this.isEditingAccount = false;
        },

        showVerifyModal(account) {
            this.verifyingAccount = account;
            this.showVerifyCodeModal = true;
        },

        async handleDelete(accountId) {
            if (confirm(this.t('confirm.delete.account'))) {
                this.$emit('delete-account', accountId);
            }
        },

        handleStart(accountId) {
            this.$emit('start-account', accountId);
        },

        async handleStop(accountId) {
            if (confirm(this.t('confirm.stop.account'))) {
                this.$emit('stop-account', accountId);
            }
        },

        async handleSaveAccount(data) {
            if (this.isEditingAccount) {
                try {
                    await accountService.updateAccount(this.editingAccount.id, data);
                    uiHelpers.showToast(this.t('toast.accountUpdated'));
                    this.closeAccountModal();
                    this.$emit('reload-accounts');
                } catch (err) {
                    alert(this.t('alert.accountUpdateFailed') + ': ' + err.message);
                }
            } else {
                this.$emit('add-account', data);
                this.closeAccountModal();
            }
        },

        handleVerified() {
            this.showVerifyCodeModal = false;
            this.$emit('reload-accounts');
        },

        async showNotifications(account) {
            try {
                const notifications = await accountService.getNotifications(account.id);
                const messages = notifications.map(n =>
                    `[${new Date(n.created_at).toLocaleString()}] ${n.message}`
                ).join('\n\n');

                alert(`${this.t('notifications.title')} ${account.name || account.phone_number}:\n\n${messages || this.t('notifications.empty')}`);

                for (const n of notifications) {
                    if (!n.is_read) {
                        await accountService.markNotificationRead(account.id, n.id);
                    }
                }

                this.$emit('reload-accounts');
            } catch (err) {
                alert(this.t('alert.notificationsLoadFailed') + ': ' + err.message);
            }
        },

        handleTopupSuccess() {
            this.$emit('reload-user');
            uiHelpers.showToast(this.t('toast.balanceTopup'));
        },

        handleAddTask(account) {
            if (account.monitoring_tasks.length >= 5) {
                alert(this.t('error.max.tasks'));
                return;
            }
            this.currentAccountId = account.id;
            this.editingTask = null;
            this.isEditingTask = false;
            this.showTaskModal = true;
        },

        handleEditTask(account, task) {
            this.currentAccountId = account.id;
            this.editingTask = {...task};
            this.isEditingTask = true;
            this.showTaskModal = true;
        },

        async handleSaveTask(data) {
            try {
                if (this.isEditingTask) {
                    await taskService.updateTask(this.currentAccountId, this.editingTask.id, data);
                    uiHelpers.showToast(this.t('toast.taskUpdated'));
                } else {
                    await taskService.createTask(this.currentAccountId, data);
                    uiHelpers.showToast(this.t('toast.taskCreated'));
                }
                this.closeTaskModal();
                this.$emit('reload-accounts');
            } catch (err) {
                alert(this.t('alert.taskSaveFailed') + ': ' + err.message);
            }
        },

        async handleStartTask(accountId, taskId) {
            try {
                await taskService.startTask(accountId, taskId);
                uiHelpers.showToast(this.t('toast.taskStarted'));
                this.$emit('reload-accounts');
            } catch (err) {
                alert(this.t('alert.taskStartFailed') + ': ' + err.message);
            }
        },

        async handleStopTask(accountId, taskId) {
            if (confirm(this.t('confirm.stop.task'))) {
                try {
                    await taskService.stopTask(accountId, taskId);
                    uiHelpers.showToast(this.t('toast.taskStopped'));
                    this.$emit('reload-accounts');
                } catch (err) {
                    alert(this.t('alert.taskStopFailed') + ': ' + err.message);
                }
            }
        },

        async handleDeleteTask(accountId, taskId) {
            if (confirm(this.t('confirm.delete.task'))) {
                try {
                    await taskService.deleteTask(accountId, taskId);
                    uiHelpers.showToast(this.t('toast.taskDeleted'));
                    this.$emit('reload-accounts');
                } catch (err) {
                    alert(this.t('alert.taskDeleteFailed') + ': ' + err.message);
                }
            }
        },

        closeTaskModal() {
            this.showTaskModal = false;
            this.editingTask = null;
            this.isEditingTask = false;
            this.currentAccountId = null;
        }
    }
};