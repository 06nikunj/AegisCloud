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
</script>

<template>
  <div class="login">
    <section class="pitch">
      <svg width="56" height="56" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 2 4 5v6c0 5 3.4 9.3 8 11 4.6-1.7 8-6 8-11V5l-8-3Z" fill="none" stroke="var(--accent)" stroke-width="1.4" stroke-linejoin="round" />
        <path d="M12 7v10M8 11h8" stroke="var(--accent)" stroke-width="1.4" stroke-linecap="round" />
      </svg>
      <h1>See what's wrong with your containers before an attacker does.</h1>
      <p class="muted">AegisCloud scans Docker images, watches running containers, and explains every threat in plain English.</p>
    </section>

    <section class="form-wrap">
      <form class="panel" @submit.prevent="submit">
        <h2>{{ isLogin ? 'Sign in' : 'Create your account' }}</h2>

        <label v-if="!isLogin">Name
          <input v-model="name" required minlength="2" autocomplete="name" />
        </label>
        <label>Email
          <input v-model="email" type="email" required autocomplete="email" />
        </label>
        <label>Password
          <input v-model="password" type="password" required minlength="8"
                 :autocomplete="isLogin ? 'current-password' : 'new-password'" />
        </label>

        <p v-if="error" class="error" role="alert">{{ error }}</p>

        <button class="btn" :disabled="busy">
          {{ busy ? 'Please wait…' : isLogin ? 'Sign in' : 'Create account' }}
        </button>

        <p class="switch muted">
          {{ isLogin ? 'New here?' : 'Already have an account?' }}
          <a href="#" @click.prevent="toggle">{{ isLogin ? 'Create an account' : 'Sign in' }}</a>
        </p>
      </form>
    </section>
  </div>
</template>

<style scoped>
.login { min-height: 100%; display: grid; grid-template-columns: 1.1fr 1fr; }
.pitch { padding: 4rem 4rem; display: flex; flex-direction: column; justify-content: center; gap: 1.25rem; max-width: 40rem; }
.pitch h1 { font-size: 2.3rem; font-weight: 700; }
.form-wrap { display: flex; align-items: center; justify-content: center; padding: 2rem; background: var(--panel); border-left: 1px solid var(--line); }
form { width: 100%; max-width: 22rem; display: flex; flex-direction: column; gap: 1rem; background: var(--bg); }
label { display: flex; flex-direction: column; gap: 0.3rem; font-size: 0.9rem; color: var(--muted); }
input {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 0.6rem 0.75rem;
  color: var(--text);
}
input:focus { border-color: var(--accent); outline: none; }
.error { color: var(--crit); font-size: 0.9rem; }
.switch { font-size: 0.9rem; text-align: center; }
@media (max-width: 820px) {
  .login { grid-template-columns: 1fr; }
  .pitch { padding: 2rem 1.5rem 1rem; }
  .pitch h1 { font-size: 1.7rem; }
  .form-wrap { border-left: 0; }
}
</style>