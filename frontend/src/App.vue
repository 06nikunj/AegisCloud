<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from './store/auth'
import Navbar from './components/Navbar.vue'
import AppFooter from './components/AppFooter.vue'

const auth = useAuthStore()
onMounted(() => auth.restore())
</script>

<template>
  <div v-if="auth.isAuthenticated" class="shell">
    <Navbar />
    <main class="content"><router-view /></main>
    <AppFooter />
  </div>
  <router-view v-else />
</template>

<style scoped>
.shell { min-height: 100%; display: flex; flex-direction: column; background: var(--bg); }
.content { flex: 1; width: 100%; max-width: 76rem; margin: 0 auto; padding: 1.75rem 2rem 1rem; }
@media (max-width: 820px) { .content { padding: 1.25rem 1rem 0.5rem; } }
</style>