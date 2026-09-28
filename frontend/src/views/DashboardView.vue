<script setup>
import { computed, onMounted } from 'vue'
import { useDashboardStore } from '../store/dashboard'
import SeverityBadge from '../components/SeverityBadge.vue'

const store = useDashboardStore()
onMounted(() => store.load())

const RADIUS = 70
const CIRC = 2 * Math.PI * RADIUS
const score = computed(() => store.summary?.risk_score ?? 0)
const dashOffset = computed(() => CIRC * (1 - score.value / 100))
const hasScans = computed(() => (store.summary?.scans_total ?? 0) > 0)
const severities = ['critical', 'high', 'medium', 'low']

const actionLabels = {
  'auth.login': 'Signed in',
  'auth.login_failed': 'Failed sign-in',
  'auth.register': 'Account created',
}
const label = (a) => actionLabels[a] || a
const when = (iso) => new Date(iso).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })
</script>

<template>
  <div class="page">
    <h1>Security overview</h1>

    <p v-if="store.error" class="error" role="alert">{{ store.error }}</p>

    <div class="top-row">
      <section class="panel risk">
        <svg viewBox="0 0 180 180" class="dial" role="img" :aria-label="`Infrastructure risk score ${score} out of 100`">
          <circle cx="90" cy="90" :r="RADIUS" fill="none" stroke="var(--line)" stroke-width="12" />
          <circle cx="90" cy="90" :r="RADIUS" fill="none" stroke="var(--accent)" stroke-width="12"
                  stroke-linecap="round" :stroke-dasharray="CIRC" :stroke-dashoffset="dashOffset"
                  transform="rotate(-90 90 90)" class="arc" />
          <text x="90" y="88" text-anchor="middle" class="score">{{ score }}</text>
          <text x="90" y="112" text-anchor="middle" class="of">out of 100</text>
        </svg>
        <div>
          <h2>Infrastructure risk</h2>
          <p class="muted">
            {{ hasScans ? 'Based on your latest image scans and runtime alerts.'
                        : 'No scans yet. Scan a Docker image to get your first risk score.' }}
          </p>
        </div>
      </section>

      <section class="panel sev">
        <h2>Vulnerabilities by severity</h2>
        <ul>
          <li v-for="s in severities" :key="s">
            <SeverityBadge :level="s" />
            <strong>{{ store.summary?.severity[s] ?? 0 }}</strong>
          </li>
        </ul>
      </section>
    </div>

    <div class="bottom-row">
      <section class="panel">
        <h2>Live threat feed</h2>
        <p class="muted empty">No runtime alerts. Falco alerts will appear here as they happen.</p>
      </section>

      <section class="panel">
        <h2>Recent activity</h2>
        <p v-if="!store.summary?.recent_activity.length" class="muted empty">Nothing recorded yet.</p>
        <ul v-else class="activity">
          <li v-for="(a, i) in store.summary.recent_activity" :key="i">
            <span>{{ label(a.action) }}<span class="muted"> · {{ a.user_email || 'unknown' }}</span></span>
            <time class="muted">{{ when(a.timestamp) }}</time>
          </li>
        </ul>
      </section>
    </div>
  </div>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: 1.25rem; max-width: 70rem; }
h1 { font-size: 1.6rem; }
h2 { font-size: 1.05rem; margin-bottom: 0.6rem; }
.error { color: var(--crit); }
.top-row { display: grid; grid-template-columns: 1.4fr 1fr; gap: 1.25rem; }
.bottom-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem; }
.risk { display: flex; align-items: center; gap: 1.75rem; }
.dial { width: 170px; flex: none; }
.arc { transition: stroke-dashoffset 0.9s ease; }
.score { fill: var(--text); font-size: 44px; font-weight: 700; }
.of { fill: var(--muted); font-size: 12px; }
.sev ul, .activity { list-style: none; margin: 0; padding: 0; }
.sev li { display: flex; justify-content: space-between; align-items: center; padding: 0.55rem 0; border-top: 1px solid var(--line); }
.sev strong { font-size: 1.3rem; }
.activity li { display: flex; justify-content: space-between; gap: 1rem; padding: 0.5rem 0; border-top: 1px solid var(--line); font-size: 0.92rem; }
.activity time { white-space: nowrap; font-size: 0.85rem; }
.empty { padding: 0.5rem 0; }
@media (max-width: 900px) {
  .top-row, .bottom-row { grid-template-columns: 1fr; }
  .risk { flex-direction: column; text-align: center; }
}
</style>