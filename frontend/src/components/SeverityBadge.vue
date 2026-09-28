<script setup>
defineProps({ level: { type: String, required: true } })
</script>

<template>
  <span class="badge" :class="level">{{ level }}</span>
</template>

<style scoped>
.badge {
  display: inline-block;
  padding: 0.1rem 0.55rem;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: capitalize;
  border: 1px solid currentColor;
}
.critical { color: var(--crit); }
.high { color: var(--high); }
.medium { color: var(--med); }
.low { color: var(--low); }
</style>