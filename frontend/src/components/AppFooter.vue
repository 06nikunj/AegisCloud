<script setup>
const year = new Date().getFullYear()
</script>

<template>
  <footer class="foot">
    <div class="inner">
      <span>&copy; {{ year }} AegisCloud &middot; Container vulnerability &amp; runtime threat defense</span>
      <nav>
        <router-link to="/monitoring">System status</router-link>
        <router-link to="/scan">Scan an image</router-link>
        <router-link to="/ai">AI analysis</router-link>
      </nav>
    </div>
  </footer>
</template>

<style scoped>
.foot { border-top: 1px solid var(--border); background: var(--surface); margin-top: 2rem; }
.inner {
  max-width: 76rem; margin: 0 auto; padding: 1.1rem 2rem;
  display: flex; justify-content: space-between; align-items: center; gap: 1rem; flex-wrap: wrap;
  font-size: 0.82rem; color: var(--muted);
}
nav { display: flex; gap: 1.25rem; }
nav a { color: var(--muted); text-decoration: none; }
nav a:hover { color: var(--secondary); }
@media (max-width: 820px) { .inner { padding: 1rem; } }
</style>