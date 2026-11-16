<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'

const auth = useAuthStore()
const router = useRouter()

const links = [
  { to: '/', label: 'Dashboard' },
  { to: '/scan', label: 'Image scans' },
  { to: '/alerts', label: 'Runtime alerts' },
  { to: '/ai', label: 'AI analysis' },
  { to: '/monitoring', label: 'Metrics' },
]

function signOut() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <header class="top">
    <div class="row">
      <div class="brand">
        <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M12 2 4 5v6c0 5 3.4 9.3 8 11 4.6-1.7 8-6 8-11V5l-8-3Z"
                fill="none" stroke="#FFFFFF" stroke-width="1.8" stroke-linejoin="round" />
          <path d="M12 7v10M8 11h8" stroke="#FFFFFF" stroke-width="1.8" stroke-linecap="round" />
        </svg>
        <span>AegisCloud<span class="dot">.</span></span>
      </div>

      <nav>
        <router-link v-for="l in links" :key="l.to" :to="l.to">{{ l.label }}</router-link>
      </nav>

      <div class="who" v-if="auth.user">
        <div class="avatar">{{ auth.user.name.charAt(0).toUpperCase() }}</div>
        <div class="who-text">
          <strong>{{ auth.user.name }}</strong>
          <span class="role">{{ auth.user.role }}</span>
        </div>
        <button class="btn-quiet" @click="signOut">Sign out</button>
      </div>
    </div>
  </header>
</template>

<style scoped>
.top {
  background: #0B2240;
  border-bottom: 1px solid #16335A;
  position: sticky;
  top: 0;
  z-index: 100;
}
.row {
  max-width: 76rem;
  margin: 0 auto;
  padding: 0.75rem 2rem;
  display: flex;
  align-items: center;
  gap: 2rem;
}
.brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 700;
  font-size: 1.05rem;
  color: #FFFFFF;
  white-space: nowrap;
}
.brand .dot { color: var(--accent); }

nav {
  display: flex;
  gap: 0.2rem;
  flex: 1;
  overflow-x: auto;
}
nav a {
  color: #9FB2CC;
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 600;
  padding: 0.5rem 0.75rem;
  border-radius: 7px;
  white-space: nowrap;
  transition: color 0.15s ease, background 0.15s ease;
}
nav a:hover { color: #FFFFFF; background: rgba(255, 255, 255, 0.06); }
nav a.router-link-exact-active { color: #FFFFFF; background: var(--secondary); }

.who { display: flex; align-items: center; gap: 0.6rem; white-space: nowrap; }
.avatar {
  width: 30px; height: 30px; border-radius: 999px;
  background: var(--accent); color: #3A2A05;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 0.82rem; flex: none;
}
.who-text { display: flex; flex-direction: column; line-height: 1.2; font-size: 0.82rem; }
.who-text strong { color: #FFFFFF; }
.role { color: #9FB2CC; text-transform: capitalize; }
.who .btn-quiet {
  background: transparent; color: #9FB2CC; border: 1px solid #2A4A72;
}
.who .btn-quiet:hover { color: #FFFFFF; border-color: #9FB2CC; }

@media (max-width: 820px) {
  .row { padding: 0.65rem 1rem; gap: 1rem; flex-wrap: wrap; }
  .who-text { display: none; }
}
</style>