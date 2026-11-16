<script setup>
/** Coloured severity pill. `level` is critical | high | medium | low (any case). */
defineProps({ level: { type: String, required: true } })
</script>

<template>
  <span class="badge sev" :class="level.toLowerCase()">{{ level.toLowerCase() }}</span>
</template>

<style scoped>
.sev { text-transform: capitalize; color: var(--muted); background: var(--surface-2); }
.critical { color: var(--crit); background: var(--crit-bg); }
.high { color: var(--high); background: var(--high-bg); }
.medium { color: #9A6700; background: var(--med-bg); }
.low { color: var(--low); background: var(--low-bg); }
</style>