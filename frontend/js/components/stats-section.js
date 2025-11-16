// frontend/js/components/stats-section.js
const StatsSectionComponent = {
    template: `
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-header">
                    <div>
                        <div class="stat-label">{{ t('stats.accounts') }}</div>
                        <div class="stat-value">{{ totalAccounts }}</div>
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
                        <div class="stat-label">{{ t('stats.tasks') }}</div>
                        <div class="stat-value">{{ totalTasks }}</div>
                    </div>
                    <div class="stat-icon" style="background: #c6f6d5;">
                        <svg viewBox="0 0 24 24" fill="#2f855a">
                            <path d="M19 3h-4.18C14.4 1.84 13.3 1 12 1c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm-2 14l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z"/>
                        </svg>
                    </div>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-header">
                    <div>
                        <div class="stat-label">{{ t('stats.errors') }}</div>
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
    `,
    props: ['totalAccounts', 'totalTasks', 'errorCount'],
    methods: {
        t(key) {
            return window.t ? window.t(key) : key;
        }
    }
};