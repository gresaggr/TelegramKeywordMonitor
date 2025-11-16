// frontend/js/components/task-list.js
const TaskListComponent = {
    template: `
        <div v-if="account.monitoring_tasks.length > 0" style="margin-top: 15px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <strong style="color: #2d3748;">{{ t('tasks.title') }}</strong>
                <button v-if="account.monitoring_tasks.length < 5 && account.status === 'active'"
                        @click="$emit('add-task')" 
                        class="btn btn-primary" 
                        style="padding: 6px 12px; font-size: 13px;">
                    + {{ t('tasks.add') }}
                </button>
            </div>
            
            <task-item-component
                v-for="task in account.monitoring_tasks"
                :key="task.id"
                :task="task"
                @edit="$emit('edit-task', task)"
                @start="$emit('start-task', task.id)"
                @stop="$emit('stop-task', task.id)"
                @delete="$emit('delete-task', task.id)"
            ></task-item-component>
        </div>
        <div v-else style="margin-top: 15px;">
            <div style="color: #718096; font-size: 14px; margin-bottom: 10px;">{{ t('tasks.empty') }}</div>
            <button v-if="account.status === 'active'"
                    @click="$emit('add-task')"
                    class="btn btn-primary"
                    style="padding: 8px 16px; font-size: 14px;">
                + {{ t('tasks.addFirst') }}
            </button>
        </div>
    `,
    props: ['account'],
    components: {
        'task-item-component': TaskItemComponent
    },
    methods: {
        t(key) {
            return window.t ? window.t(key) : key;
        }
    }
};