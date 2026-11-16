<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'

const auth = useAuthStore()
const router = useRouter()

const mode = ref('login')
const name = ref('')
const email = ref('')
const password = ref('')
const showPassword = ref(false)
const error = ref('')
const busy = ref(false)

const isLogin = computed(() => mode.value === 'login')

function toggle() {
  mode.value = isLogin.value ? 'register' : 'login'
  error.value = ''
}

async function submit() {
  error.value = ''
  busy.value = true
  try {
    if (isLogin.value) await auth.login(email.value, password.value)
    else await auth.register(name.value, email.value, password.value)
    router.push({ name: 'dashboard' })
  } catch (e) {
    const detail = e.response?.data?.detail
    error.value = typeof detail === 'string'
      ? detail
      : e.response ? 'Check your details. The password needs at least 8 characters.'
      : "Can't reach the server. Check that the API is running."
  } finally {
    busy.value = false
  }
}

const features = [
  {
    icon: 'scan',
    title: 'Vulnerability Scanning',
    text: 'Every Docker image is checked against the latest CVE database before it ever reaches production.',
  },
  {
    icon: 'shield',
    title: 'Runtime Protection',
    text: 'Live containers are watched continuously, with instant alerts the moment something looks wrong.',
  },
]
</script>

<template>
  <div class="page">
    <header class="brand-bar">
      <svg width="26" height="26" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 2 4 5v6c0 5 3.4 9.3 8 11 4.6-1.7 8-6 8-11V5l-8-3Z"
              fill="none" stroke="var(--primary)" stroke-width="1.8" stroke-linejoin="round" />
        <path d="M12 7v10M8 11h8" stroke="var(--primary)" stroke-width="1.8" stroke-linecap="round" />
      </svg>
      <span>AegisCloud</span>
    </header>

    <main class="layout">
      <!-- Login card -->
      <section class="card login-card">
        <div class="icon-badge">
          <svg width="30" height="30" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 2 4 5v6c0 5 3.4 9.3 8 11 4.6-1.7 8-6 8-11V5l-8-3Z" fill="#fff" />
            <path d="M12 2 4 5v6c0 5 3.4 9.3 8 11 4.6-1.7 8-6 8-11V5l-8-3Z"
                  fill="none" stroke="#fff" stroke-width="0.5" />
            <rect x="9.3" y="10.6" width="5.4" height="4.4" rx="0.9" fill="var(--primary)" />
            <path d="M10.3 10.6v-1.3a1.7 1.7 0 0 1 3.4 0v1.3" fill="none" stroke="var(--primary)" stroke-width="1.1" />
          </svg>
        </div>

        <h1>AegisCloud</h1>
        <p class="sub muted">{{ isLogin ? 'Sign in to your security console' : 'Create your security console account' }}</p>

        <form @submit.prevent="submit">
          <label v-if="!isLogin">Name
            <div class="input-wrap">
              <svg class="input-icon" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
                <circle cx="12" cy="8" r="3.4" fill="none" stroke="currentColor" stroke-width="1.6" />
                <path d="M5 20c1.2-3.6 4-5.4 7-5.4s5.8 1.8 7 5.4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
              </svg>
              <input v-model="name" required minlength="2" autocomplete="name" placeholder="Your full name" />
            </div>
          </label>

          <label>Email
            <div class="input-wrap">
              <svg class="input-icon" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
                <rect x="3.5" y="5.5" width="17" height="13" rx="2" fill="none" stroke="currentColor" stroke-width="1.6" />
                <path d="M4.5 7 12 12.5 19.5 7" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              <input v-model="email" type="email" required autocomplete="email" placeholder="you@company.com" />
            </div>
          </label>

          <label>Password
            <div class="input-wrap">
              <svg class="input-icon" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
                <rect x="5.5" y="10.5" width="13" height="9" rx="1.8" fill="none" stroke="currentColor" stroke-width="1.6" />
                <path d="M8.3 10.5V8a3.7 3.7 0 0 1 7.4 0v2.5" fill="none" stroke="currentColor" stroke-width="1.6" />
              </svg>
              <input
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                required minlength="8" placeholder="Password"
                :autocomplete="isLogin ? 'current-password' : 'new-password'"
              />
              <button type="button" class="eye" @click="showPassword = !showPassword"
                      :aria-label="showPassword ? 'Hide password' : 'Show password'">
                <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
                  <path v-if="!showPassword" d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7-10-7-10-7Z" fill="none" stroke="currentColor" stroke-width="1.6" />
                  <circle v-if="!showPassword" cx="12" cy="12" r="3" fill="none" stroke="currentColor" stroke-width="1.6" />
                  <path v-else d="M3 3l18 18M9.9 9.9a3 3 0 0 0 4.2 4.2M6.2 6.6C3.9 8.1 2 12 2 12s3.6 7 10 7c1.9 0 3.5-.6 4.9-1.4M17.8 17.4C19.9 15.9 22 12 22 12s-1.3-2.5-3.6-4.4"
                        fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
                </svg>
              </button>
            </div>
          </label>

          <p v-if="error" class="error" role="alert">{{ error }}</p>

          <button class="btn-primary" :disabled="busy">
            {{ busy ? 'Please wait…' : isLogin ? 'Log in' : 'Create account' }}
          </button>

          <p class="switch muted">
            {{ isLogin ? "Don't have an account?" : 'Already have an account?' }}
            <a href="#" @click.prevent="toggle">{{ isLogin ? 'Sign up' : 'Sign in' }}</a>
          </p>
        </form>
      </section>

      <!-- Feature panels -->
      <section class="side">
        <div class="card feature" v-for="f in features" :key="f.title">
          <div class="feature-icon">
            <svg v-if="f.icon === 'scan'" width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">
              <rect x="4" y="4" width="16" height="16" rx="2.5" fill="none" stroke="var(--secondary)" stroke-width="1.7" />
              <path d="M8 12h8M12 8v8" stroke="var(--secondary)" stroke-width="1.7" stroke-linecap="round" />
            </svg>
            <svg v-else width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 2 4 5v6c0 5 3.4 9.3 8 11 4.6-1.7 8-6 8-11V5l-8-3Z" fill="none" stroke="var(--secondary)" stroke-width="1.7" stroke-linejoin="round" />
              <path d="m9 12 2 2 4-4" stroke="var(--secondary)" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" fill="none" />
            </svg>
          </div>
          <h2>{{ f.title }}</h2>
          <p class="muted">{{ f.text }}</p>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.page { min-height: 100%; background: var(--bg); display: flex; flex-direction: column; }

.brand-bar {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 1.25rem 2.5rem; font-weight: 700; font-size: 1.1rem; color: var(--primary);
}

.layout {
  flex: 1;
  width: 100%;
  max-width: 68rem;
  margin: 0 auto;
  padding: 1rem 2.5rem 3rem;
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  gap: 1.5rem;
  align-items: start;
}

.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04), 0 8px 24px rgba(16, 24, 40, 0.06);
}

.login-card { padding: 2.25rem 2.25rem 2rem; text-align: center; }
.icon-badge {
  width: 56px; height: 56px; border-radius: 999px; margin: 0 auto 1rem;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
}
.login-card h1 { font-size: 1.5rem; }
.sub { margin-top: 0.3rem; margin-bottom: 1.6rem; font-size: 0.92rem; }

form { display: flex; flex-direction: column; gap: 1rem; text-align: left; }
label { display: flex; flex-direction: column; gap: 0.35rem; font-size: 0.85rem; font-weight: 600; color: var(--ink); }

.input-wrap {
  position: relative; display: flex; align-items: center;
  background: var(--surface-2); border: 1px solid var(--border); border-radius: 9px;
}
.input-wrap:focus-within { border-color: var(--secondary); background: var(--surface); }
.input-icon { margin-left: 0.7rem; color: var(--muted); flex: none; }
.input-wrap input {
  border: 0; background: transparent; padding: 0.65rem 0.7rem; width: 100%;
  color: var(--ink); outline: none;
}
.eye {
  background: none; border: 0; color: var(--muted); cursor: pointer;
  display: flex; align-items: center; padding: 0 0.7rem;
}
.eye:hover { color: var(--secondary); }

.error { color: var(--crit); font-size: 0.85rem; margin: 0; }

.btn-primary {
  border: 0; border-radius: 9px; padding: 0.75rem 1rem; font-weight: 700; font-size: 0.96rem;
  color: #3A2A05; cursor: pointer;
  background: linear-gradient(135deg, #FFC978, var(--accent));
}
.btn-primary:hover { filter: brightness(1.04); }
.btn-primary:disabled { opacity: 0.6; cursor: default; }

.switch { text-align: center; font-size: 0.88rem; margin: 0; }
.switch a { font-weight: 600; }

.side { display: flex; flex-direction: column; gap: 1.25rem; }
.feature { padding: 1.5rem; }
.feature-icon {
  width: 44px; height: 44px; border-radius: 10px; margin-bottom: 0.9rem;
  display: flex; align-items: center; justify-content: center;
  background: #EAF1F8;
}
.feature h2 { font-size: 1.05rem; margin-bottom: 0.4rem; }
.feature p { font-size: 0.88rem; line-height: 1.5; }

@media (max-width: 860px) {
  .layout { grid-template-columns: 1fr; padding: 1rem 1.25rem 2rem; }
  .brand-bar { padding: 1rem 1.25rem; }
}
</style>