// frontend/js/components/task-item.js
const TaskItemComponent = {
    template: `
        <div style="background: #f7fafc; padding: 12px; border-radius: 8px; margin-bottom: 8px; border-left: 3px solid #667eea;">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div style="flex: 1;">
                    <div style="font-weight: 600; color: #2d3748; margin-bottom: 5px;">
                        {{ task.name }}
                        <span :class="task.is_active ? 'status-badge status-active' : 'status-badge status-stopped'" 
                              style="margin-left: 8px; font-size: 11px;">
                            {{ task.is_active ? 'Active' : 'Inactive' }}
                        </span>
                    </div>
                    
                    <div v-if="isExpanded" class="site-info-grid" style="margin-top: 8px;">
                        <div class="site-info-label">Channels:</div>
                        <div class="site-info-value">{{ task.monitored_channels.join(', ') }}</div>
                        
                        <div class="site-info-label">Forward to:</div>
                        <div class="site-info-value">{{ task.forward_to_chat_id }}</div>
                        
                        <div class="site-info-label">Whitelist:</div>
                        <div class="site-info-value">
                            <template v-if="task.whitelist_keywords.length > 0">
                                {{ task.whitelist_keywords.join(', ') }}
                            </template>
                            <template v-else>All messages</template>
                        </div>
                        
                        <div class="site-info-label">Blacklist:</div>
                        <div class="site-info-value">
                            <template v-if="task.blacklist_keywords.length > 0">
                                {{ task.blacklist_keywords.join(', ') }}
                            </template>
                            <template v-else>None</template>
                        </div>
                    </div>
                    
                    <button @click="isExpanded = !isExpanded" class="btn-toggle-details" style="margin-top: 8px;">
                        <span>{{ isExpanded ? 'Hide details' : 'Show details' }}</span>
                        <svg viewBox="0 0 24 24" :class="{ 'rotate-180': isExpanded }">
                            <path d="M7 10l5 5 5-5z"/>
                        </svg>
                    </button>
                </div>
                
                <div style="display: flex; gap: 5px; margin-left: 10px;">
                    <button v-if="task.is_active"
                            @click="$emit('stop')" 
                            class="btn-icon" 
                            title="Stop Task">
                        <svg viewBox="0 0 24 24">
                            <path d="M6 6h12v12H6z"/>
                        </svg>
                    </button>
                    <button v-else
                            @click="$emit('start')" 
                            class="btn-icon" 
                            title="Start Task">
                        <svg viewBox="0 0 24 24">
                            <path d="M8 5v14l11-7z"/>
                        </svg>
                    </button>
                    <button @click="$emit('edit')" class="btn-icon" title="Edit Task">
                        <svg viewBox="0 0 24 24">
                            <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
                        </svg>
                    </button>
                    <button @click="$emit('delete')" class="btn-icon btn-icon-danger" title="Delete Task">
                        <svg viewBox="0 0 24 24">
                            <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    `,
    props: ['task'],
    data() {
        return {
            isExpanded: false
        };
    }
};