<script setup>
/** Page title block with breadcrumb and an actions slot (buttons on the right). */
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  crumb: { type: String, default: '' },
})
</script>

<template>
  <div class="ph">
    <div class="ph-text">
      <nav class="crumbs" aria-label="Breadcrumb">
        <router-link to="/">AegisCloud</router-link>
        <template v-if="crumb"><span class="sep">/</span><span class="here">{{ crumb }}</span></template>
      </nav>
      <h1>{{ title }}</h1>
      <p v-if="subtitle" class="muted subtitle">{{ subtitle }}</p>
    </div>
    <div class="ph-actions"><slot /></div>
  </div>
</template>

<style scoped>
.ph { display: flex; justify-content: space-between; align-items: flex-end; gap: 1rem; flex-wrap: wrap; margin-bottom: 0.25rem; }
.crumbs { font-size: 0.8rem; margin-bottom: 0.35rem; display: flex; gap: 0.4rem; }
.crumbs a { color: var(--muted); text-decoration: none; }
.crumbs a:hover { color: var(--secondary); }
.sep { color: var(--border-strong); }
.here { color: var(--ink); font-weight: 600; }
h1 { font-size: 1.65rem; }
.subtitle { margin-top: 0.2rem; font-size: 0.93rem; }
.ph-actions { display: flex; gap: 0.6rem; flex-wrap: wrap; }
</style>