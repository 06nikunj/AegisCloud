<script setup>
const links = [
  { to: '/', label: 'Dashboard' },
  { to: '/scan', label: 'Image scans' },
  { to: '/alerts', label: 'Runtime alerts' },
  { to: '/ai', label: 'AI analysis' },
  { to: '/monitoring', label: 'Metrics' },
]
</script>

<template>
  <aside class="side">
    <div class="brand">
      <svg width="26" height="26" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 2 4 5v6c0 5 3.4 9.3 8 11 4.6-1.7 8-6 8-11V5l-8-3Z" fill="none" stroke="var(--accent)" stroke-width="1.8" stroke-linejoin="round" />
        <path d="M12 7v10M8 11h8" stroke="var(--accent)" stroke-width="1.8" stroke-linecap="round" />
      </svg>
      <span>AegisCloud</span>
    </div>
    <nav>
      <router-link v-for="l in links" :key="l.to" :to="l.to">{{ l.label }}</router-link>
    </nav>
  </aside>
</template>

<style scoped>
.side { background: var(--panel); border-right: 1px solid var(--line); padding: 1.25rem 0.9rem; }
.brand { display: flex; align-items: center; gap: 0.6rem; font-weight: 700; font-size: 1.1rem; padding: 0 0.5rem 1.5rem; }
nav { display: flex; flex-direction: column; gap: 0.15rem; }
nav a {
  color: var(--muted);
  text-decoration: none;
  padding: 0.55rem 0.7rem;
  border-radius: 8px;
  border-left: 3px solid transparent;
}
nav a:hover { color: var(--text); background: var(--panel-2); }
nav a.router-link-exact-active { color: var(--text); background: var(--panel-2); border-left-color: var(--accent); }
@media (max-width: 820px) {
  .side { border-right: 0; border-bottom: 1px solid var(--line); padding: 0.8rem; }
  .brand { padding-bottom: 0.7rem; }
  nav { flex-direction: row; overflow-x: auto; }
  nav a { white-space: nowrap; border-left: 0; }
}
</style>