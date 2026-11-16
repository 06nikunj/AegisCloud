<script setup>
import { computed, onMounted, ref } from 'vue'
import { useDashboardStore } from '../store/dashboard'
import { listScans } from '../services/scanService'
import { listAlerts } from '../services/alertService'
import { timeAgo, riskBadgeClass, riskLabelFor } from '../utils/format'
import PageHeader from '../components/PageHeader.vue'
import AppIcon from '../components/AppIcon.vue'
import SeverityBadge from '../components/SeverityBadge.vue'

const store = useDashboardStore()
const scans = ref([])
const alerts = ref([])
const refreshing = ref(false)

/** Load the summary, recent scans and alerts together; one failing call never blocks the others. */
async function reload() {
  refreshing.value = true
  const [, s, a] = await Promise.allSettled([store.load(), listScans(), listAlerts()])
  scans.value = s.status === 'fulfilled' ? s.value : []
  alerts.value = a.status === 'fulfilled' ? a.value : []
  refreshing.value = false
}
onMounted(reload)

/* ---- risk gauge ---- */
const RADIUS = 58
const CIRC = 2 * Math.PI * RADIUS
const score = computed(() => store.summary?.risk_score ?? 0)
const hasScans = computed(() => (store.summary?.scans_total ?? 0) > 0)
const dashOffset = computed(() => CIRC * (1 - score.value / 100))
const riskLabel = computed(() => (hasScans.value ? riskLabelFor(score.value) : 'No data'))
const riskBadge = computed(() => (hasScans.value ? riskBadgeClass(score.value) : 'badge-neutral'))
const gaugeColor = computed(() => {
  if (score.value < 20) return 'var(--low)'
  if (score.value < 50) return 'var(--med)'
  if (score.value < 80) return 'var(--high)'
  return 'var(--crit)'
})

/* ---- severity breakdown ---- */
const severities = [
  { key: 'critical', label: 'Critical', color: 'var(--crit)' },
  { key: 'high', label: 'High', color: 'var(--high)' },
  { key: 'medium', label: 'Medium', color: 'var(--med)' },
  { key: 'low', label: 'Low', color: 'var(--low)' },
]
const severity = computed(() => store.summary?.severity ?? { critical: 0, high: 0, medium: 0, low: 0 })
const vulnTotal = computed(() => Object.values(severity.value).reduce((a, b) => a + b, 0))
const segments = computed(() =>
  severities.map((s) => {
    const count = severity.value[s.key] ?? 0
    return { ...s, count, pct: vulnTotal.value ? (count / vulnTotal.value) * 100 : 0 }
  }))

const kpis = computed(() => [
  { label: 'Images scanned', value: store.summary?.scans_total ?? 0, sub: 'Total scans run', icon: 'scan', tint: 'blue' },
  { label: 'Vulnerabilities', value: vulnTotal.value, sub: 'Across all scans', icon: 'bug', tint: 'amber' },
  { label: 'Open alerts', value: store.summary?.alerts_total ?? 0, sub: 'Awaiting acknowledgement', icon: 'bell', tint: 'red' },
])

const actions = [
  { to: '/scan', label: 'Scan an image', hint: 'Find CVEs in a Docker image', icon: 'scan', tint: 'blue' },
  { to: '/alerts', label: 'Review alerts', hint: 'Runtime threats from containers', icon: 'bell', tint: 'red' },
  { to: '/ai', label: 'Analyze with AI', hint: 'Plain-English explanations', icon: 'spark', tint: 'amber' },
  { to: '/monitoring', label: 'Check system health', hint: 'Services and response times', icon: 'pulse', tint: 'green' },
]

const recentScans = computed(() => scans.value.slice(0, 5))
const openAlerts = computed(() => alerts.value.filter((a) => !a.acknowledged).slice(0, 5))

const actionLabels = {
  'auth.login': 'Signed in',
  'auth.login_failed': 'Failed sign-in',
  'auth.register': 'Account created',
  'scan.completed': 'Image scanned',
  'alerts.acknowledged': 'Alert acknowledged',
  'alerts.simulated': 'Simulated alert generated',
  'ai.analyzed': 'AI analysis run',
}
const label = (a) => actionLabels[a] || a
</script>

<template>
  <div class="page">
    <PageHeader title="Security overview" crumb="Dashboard"
                subtitle="Posture of your container images and running workloads at a glance.">
      <button class="btn btn-outline" :disabled="refreshing" @click="reload">
        <AppIcon name="refresh" :size="16" />{{ refreshing ? 'Refreshing…' : 'Refresh' }}
      </button>
      <router-link to="/scan" class="btn btn-brand"><AppIcon name="scan" :size="16" />New scan</router-link>
    </PageHeader>

    <p v-if="store.error" class="banner-error" role="alert">{{ store.error }}</p>

    <section class="kpis">
      <article v-for="k in kpis" :key="k.label" class="card kpi">
        <div class="kpi-top">
          <span class="kpi-label">{{ k.label }}</span>
          <span class="icon-tile" :class="k.tint"><AppIcon :name="k.icon" /></span>
        </div>
        <div class="kpi-value">{{ k.value }}</div>
        <div class="kpi-sub">{{ k.sub }}</div>
      </article>

      <article class="card kpi gauge">
        <div class="kpi-top">
          <span class="kpi-label">Risk score</span>
          <span class="badge" :class="riskBadge">{{ riskLabel }}</span>
        </div>
        <svg viewBox="0 0 150 150" class="dial" role="img" :aria-label="`Risk score ${score} out of 100`">
          <circle cx="75" cy="75" :r="RADIUS" fill="none" stroke="var(--surface-2)" stroke-width="12" />
          <circle cx="75" cy="75" :r="RADIUS" fill="none" :stroke="gaugeColor" stroke-width="12"
                  stroke-linecap="round" :stroke-dasharray="CIRC" :stroke-dashoffset="dashOffset"
                  transform="rotate(-90 75 75)" class="arc" />
          <text x="75" y="80" text-anchor="middle" class="score">{{ score }}</text>
          <text x="75" y="99" text-anchor="middle" class="score-of">out of 100</text>
        </svg>
      </article>
    </section>

    <section class="row-2">
      <article class="card">
        <header class="card-head">
          <h2>Vulnerabilities by severity</h2>
          <span class="muted small">{{ vulnTotal }} total</span>
        </header>
        <div class="card-body">
          <div v-if="!vulnTotal" class="empty">
            <strong>No scan data yet</strong>
            Run your first image scan to see the severity breakdown.
          </div>
          <template v-else>
            <div class="stack" role="img" aria-label="Severity distribution">
              <div v-for="s in segments" :key="s.key" class="seg" :style="{ width: s.pct + '%', background: s.color }"></div>
            </div>
            <ul class="legend">
              <li v-for="s in segments" :key="s.key">
                <span class="swatch" :style="{ background: s.color }"></span>
                <span class="legend-name">{{ s.label }}</span>
                <span class="legend-count">{{ s.count }}</span>
                <span class="legend-pct muted">{{ s.pct.toFixed(0) }}%</span>
              </li>
            </ul>
          </template>
        </div>
      </article>

      <article class="card">
        <header class="card-head"><h2>Get started</h2></header>
        <div class="card-body tiles">
          <router-link v-for="a in actions" :key="a.to" :to="a.to" class="tile">
            <span class="icon-tile" :class="a.tint"><AppIcon :name="a.icon" /></span>
            <span class="tile-title">{{ a.label }}</span>
            <span class="tile-hint">{{ a.hint }}</span>
          </router-link>
        </div>
      </article>
    </section>

    <section class="row-2">
      <article class="card">
        <header class="card-head">
          <h2>Recent scans</h2>
          <router-link to="/scan" class="link small">View all</router-link>
        </header>
        <div v-if="!recentScans.length" class="empty"><strong>No scans yet</strong>Scanned images will appear here.</div>
        <div v-else class="table-wrap">
          <table class="table">
            <thead><tr><th>Image</th><th>Scanned</th><th>Findings</th><th>Risk</th></tr></thead>
            <tbody>
              <tr v-for="s in recentScans" :key="s.id">
                <td class="strong">{{ s.image }}</td>
                <td class="muted">{{ timeAgo(s.scanned_at) }}</td>
                <td>{{ s.total }}</td>
                <td><span class="badge" :class="riskBadgeClass(s.risk_score)">{{ s.risk_score }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>

      <article class="card">
        <header class="card-head">
          <h2>Open alerts</h2>
          <router-link to="/alerts" class="link small">View all</router-link>
        </header>
        <div v-if="!openAlerts.length" class="empty"><strong>No open alerts</strong>Runtime detections will appear here.</div>
        <ul v-else class="alert-list">
          <li v-for="a in openAlerts" :key="a.id">
            <SeverityBadge :level="a.priority" />
            <div class="alert-text">
              <span class="strong">{{ a.rule }}</span>
              <span class="muted small">{{ a.container_name }} · {{ timeAgo(a.detected_at) }}</span>
            </div>
          </li>
        </ul>
      </article>
    </section>

    <article class="card">
      <header class="card-head"><h2>Recent activity</h2></header>
      <div v-if="!store.summary?.recent_activity.length" class="empty"><strong>Nothing recorded yet</strong></div>
      <ul v-else class="activity">
        <li v-for="(a, i) in store.summary.recent_activity" :key="i">
          <span>{{ label(a.action) }}<span class="muted"> · {{ a.user_email || 'system' }}</span></span>
          <time class="muted small">{{ timeAgo(a.timestamp) }}</time>
        </li>
      </ul>
    </article>
  </div>
</template>

<style scoped>
.small { font-size: 0.82rem; }
.strong { font-weight: 600; color: var(--ink); }
.link { text-decoration: none; font-weight: 600; }
.link:hover { text-decoration: underline; }

.kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.1rem; }
.kpi { padding: 1.1rem 1.25rem; display: flex; flex-direction: column; gap: 0.35rem; }
.kpi-top { display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; }
.kpi-label { font-size: 0.82rem; font-weight: 600; color: var(--muted); }
.kpi-value { font-size: 2.2rem; font-weight: 700; color: var(--primary); line-height: 1.1; }
.kpi-sub { font-size: 0.8rem; color: var(--muted); }
.gauge { align-items: stretch; }
.dial { width: 132px; align-self: center; }
.arc { transition: stroke-dashoffset 0.9s ease; }
.score { fill: var(--primary); font-size: 30px; font-weight: 700; }
.score-of { fill: var(--muted); font-size: 10px; }

.row-2 { display: grid; grid-template-columns: 1.25fr 1fr; gap: 1.1rem; align-items: start; }

.stack { display: flex; height: 14px; border-radius: 999px; overflow: hidden; background: var(--surface-2); }
.seg { height: 100%; transition: width 0.6s ease; }
.legend { list-style: none; margin: 1.1rem 0 0; padding: 0; display: flex; flex-direction: column; }
.legend li {
  display: grid; grid-template-columns: 14px 1fr auto 3rem; align-items: center; gap: 0.75rem;
  padding: 0.6rem 0; border-top: 1px solid var(--border); font-size: 0.92rem;
}
.legend li:first-child { border-top: 0; }
.swatch { width: 10px; height: 10px; border-radius: 3px; }
.legend-count { font-weight: 700; }
.legend-pct { text-align: right; font-size: 0.82rem; }

.tiles { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.tile {
  display: flex; flex-direction: column; gap: 0.4rem; padding: 0.9rem; border-radius: 10px;
  border: 1px solid var(--border); background: var(--surface-2); text-decoration: none; color: var(--ink);
  transition: border-color 0.15s, box-shadow 0.15s, transform 0.15s;
}
.tile:hover { border-color: var(--secondary); background: var(--surface); box-shadow: var(--shadow-md); transform: translateY(-1px); }
.tile-title { font-weight: 700; font-size: 0.9rem; margin-top: 0.2rem; }
.tile-hint { font-size: 0.8rem; color: var(--muted); line-height: 1.4; }

.alert-list, .activity { list-style: none; margin: 0; padding: 0; }
.alert-list li { display: flex; align-items: center; gap: 0.8rem; padding: 0.8rem 1.25rem; border-top: 1px solid var(--border); }
.alert-list li:first-child { border-top: 0; }
.alert-text { display: flex; flex-direction: column; min-width: 0; }
.activity li {
  display: flex; justify-content: space-between; gap: 1rem; padding: 0.7rem 1.25rem;
  border-top: 1px solid var(--border); font-size: 0.92rem;
}
.activity li:first-child { border-top: 0; }
.activity time { white-space: nowrap; }

@media (max-width: 1000px) {
  .kpis { grid-template-columns: repeat(2, 1fr); }
  .row-2 { grid-template-columns: 1fr; }
}
@media (max-width: 560px) {
  .kpis, .tiles { grid-template-columns: 1fr; }
}
</style>