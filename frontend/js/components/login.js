const LoginComponent = {
    template: `
        <div class="auth-wrapper">
            <div class="auth-card">
                <div class="auth-icon">
                    <svg viewBox="0 0 24 24">
                        <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                    </svg>
                </div>
                <h1 class="auth-title">Website Monitor</h1>
                <p class="auth-subtitle">Sign in to your account</p>

                <div v-if="error" class="alert alert-error">
                    <svg style="width: 20px; height: 20px; flex-shrink: 0;" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
                    </svg>
                    <span>{{ error }}</span>
                </div>

                <div class="form-group">
                    <label class="form-label">Email</label>
                    <input
                        v-model="email"
                        type="email"
                        class="form-input"
                        placeholder="your@email.com"
                        @keyup.enter="submit"
                        required
                    >
                </div>

                <div class="form-group">
                    <label class="form-label">Password</label>
                    <div class="password-input-wrapper">
                        <input
                            v-model="password"
                            :type="showPassword ? 'text' : 'password'"
                            class="form-input"
                            placeholder="••••••••"
                            @keyup.enter="submit"
                            required
                        >
                        <button @click="showPassword = !showPassword" class="password-toggle" type="button">
                            <svg v-if="!showPassword" viewBox="0 0 24 24" width="20" height="20">
                                <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
                            </svg>
                            <svg v-else viewBox="0 0 24 24" width="20" height="20">
                                <path d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z"/>
                            </svg>
                        </button>
                    </div>
                </div>

                <button @click="submit" :disabled="loading" class="btn btn-primary">
                    {{ loading ? 'Signing in...' : 'Sign In' }}
                </button>

                <div class="auth-switch">
                    Don't have an account?
                    <a @click="$emit('switch-to-register')" class="auth-link">Register</a>
                </div>
            </div>
        </div>
    `,
    props: ['error', 'loading'],
    data() {
        return {
            email: '',
            password: '',
            showPassword: false
        };
    },
    methods: {
        submit() {
            if (this.email && this.password) {
                this.$emit('login', {email: this.email, password: this.password});
            }
        }
    }
};