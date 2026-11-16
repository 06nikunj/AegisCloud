<script setup>
/** Small inline icon set. Usage: <AppIcon name="scan" :size="18" /> */
defineProps({
  name: { type: String, required: true },
  size: { type: Number, default: 18 },
})
</script>

<template>
  <svg :width="size" :height="size" viewBox="0 0 24 24" fill="none" stroke="currentColor"
       stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <template v-if="name === 'scan'"><rect x="4" y="4" width="16" height="16" rx="2.5" /><path d="M8 12h8M12 8v8" /></template>
    <template v-else-if="name === 'bug'"><ellipse cx="12" cy="13" rx="5" ry="6" /><path d="M9 7 7 5M15 7l2-2M4 12h3M17 12h3M6 18l2.5-2M18 18l-2.5-2" /></template>
    <template v-else-if="name === 'bell'"><path d="M6 10a6 6 0 1 1 12 0c0 4 1.5 5.5 1.5 5.5h-15S6 14 6 10Z" /><path d="M10 19a2 2 0 0 0 4 0" /></template>
    <template v-else-if="name === 'spark'"><path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M18 6l-2.5 2.5M8.5 15.5 6 18" /></template>
    <template v-else-if="name === 'pulse'"><path d="M3 12h3l2-6 4 12 2-8 2 4h5" /></template>
    <template v-else-if="name === 'shield'"><path d="M12 2 4 5v6c0 5 3.4 9.3 8 11 4.6-1.7 8-6 8-11V5l-8-3Z" /><path d="m9 12 2 2 4-4" /></template>
    <template v-else-if="name === 'refresh'"><path d="M20 11a8 8 0 1 0-2.3 5.7" /><path d="M20 4v7h-7" /></template>
    <template v-else-if="name === 'check'"><path d="m5 12 5 5 9-10" /></template>
    <template v-else-if="name === 'search'"><circle cx="11" cy="11" r="6" /><path d="m20 20-4-4" /></template>
    <template v-else-if="name === 'terminal'"><rect x="3" y="4" width="18" height="16" rx="2.5" /><path d="m7 10 3 2-3 2M13 15h4" /></template>
  </svg>
</template>