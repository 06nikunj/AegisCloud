<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'

const auth = useAuthStore()
const router = useRouter()

function signOut() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <header class="top">
    <div v-if="auth.user" class="who">
      <strong>{{ auth.user.name }}</strong>
      <span class="role">{{ auth.user.role }}</span>
    </div>
    <button class="btn-quiet" @click="signOut">Sign out</button>
  </header>
</template>

<style scoped>
.top { display: flex; justify-content: flex-end; align-items: center; gap: 1rem; padding: 0.9rem 2rem; border-bottom: 1px solid var(--line); }
.who { display: flex; align-items: center; gap: 0.6rem; }
.role { color: var(--muted); font-size: 0.85rem; border: 1px solid var(--line); border-radius: 999px; padding: 0 0.6rem; }
@media (max-width: 820px) { .top { padding: 0.7rem 1rem; } }
</style>