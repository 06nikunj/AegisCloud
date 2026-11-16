<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { listAlerts, acknowledgeAlert } from '../services/alertService'
import { formatDateTime, timeAgo } from '../utils/format'
import PageHeader from '../components/PageHeader.vue'
import AppIcon from '../components/AppIcon.vue'
import SeverityBadge from '../components/SeverityBadge.vue'

const alerts = ref([])
const loading = ref(false)
const error = ref('')
const acking = ref(new Set())
const statusFilter = ref('open') // open | ack | all
const severityFilter = ref('all')
const live = ref(false)
let timer = null

/** Fetch alerts. `silent` skips the loading state so live refresh doesn't flicker. */
async function load(silent = false) {
  if (!silent) loading.value = true
  error.value = ''
  try {
    alerts.value = await listAlerts()
  } catch {
    error.value = "Couldn't load alerts. Check that the backend is running."
  } finally {
    loading.value = false
  }
}

async function ack(alert) {
  acking.value.add(alert.id)
  try {
    const updated = await acknowledgeAlert(alert.id)
    const i = alerts.value.findIndex((a) => a.id === alert.id)
    if (i !== -1) alerts.value[i] = updated
  } finally {
    acking.value.delete(alert.id)
  }
}

// Live mode polls every 8 seconds so new alerts appear without a manual refresh.
watch(live, (on) => {
  clearInterval(timer)
  if (on) timer = setInterval(() => load(true), 8000)
})
onMounted(() => load())
onUnmounted(() => clearInterval(timer))

const counts = computed(() => ({
  total: alerts.value.length,
  open: alerts.value.filter((a) => !a.acknowledged).length,
  critical: alerts.value.filter((a) => !a.acknowledged && a.priority === 'critical').length,
}))

const visible = computed(() =>
  alerts.value.filter((a) =>
    (statusFilter.value === 'all' || (statusFilter.value === 'open' ? !a.acknowledged : a.acknowledged)) &&
    (severityFilter.value === 'all' || a.priority === severityFilter.value)))
</script>

<template>
  <div class="page">
    <PageHeader title="Runtime alerts" crumb="Runtime alerts"
                subtitle="Threat detections from running containers. Falco in production, simulated in this demo.">
      <label class="live" :class="{ on: live }">
        <input v-model="live" type="checkbox" />
        <span class="dot"></span>Live updates
      </label>
      <button class="btn btn-outline" :disabled="loading" @click="load()">
        <AppIcon name="refresh" :size="16" />Refresh
      </button>
    </PageHeader>

    <section class="summary">
      <div class="card stat"><span class="stat-label">Total alerts</span><span class="stat-value">{{ counts.total }}</span></div>
      <div class="card stat"><span class="stat-label">Open</span><span class="stat-value">{{ counts.open }}</span></div>
      <div class="card stat"><span class="stat-label">Critical &amp; open</span><span class="stat-value crit">{{ counts.critical }}</span></div>
    </section>

    <section class="toolbar">
      <div class="seg-group" role="tablist" aria-label="Status filter">
        <button class="chip" :class="{ active: statusFilter === 'open' }" @click="statusFilter = 'open'">Open</button>
        <button class="chip" :class="{ active: statusFilter === 'ack' }" @click="statusFilter = 'ack'">Acknowledged</button>
        <button class="chip" :class="{ active: statusFilter === 'all' }" @click="statusFilter = 'all'">All</button>
      </div>
      <select v-model="severityFilter" class="select sev-select" aria-label="Severity filter">
        <option value="all">All severities</option>
        <option value="critical">Critical</option>
        <option value="high">High</option>
        <option value="medium">Medium</option>
        <option value="low">Low</option>
      </select>
    </section>

    <p v-if="error" class="banner-error" role="alert">{{ error }}</p>
    <div v-else-if="loading && !alerts.length" class="card empty">Loading…</div>
    <div v-else-if="!alerts.length" class="card empty">
      <strong>No alerts yet</strong>
      Run <code>python scripts/simulate_falco_attack.py</code> in the backend folder to generate a demo feed.
    </div>
    <div v-else-if="!visible.length" class="card empty"><strong>Nothing matches these filters</strong></div>

    <div v-else class="list">
      <article v-for="a in visible" :key="a.id" class="card alert" :class="{ done: a.acknowledged }">
        <div class="alert-top">
          <SeverityBadge :level="a.priority" />
          <strong class="rule">{{ a.rule }}</strong>
          <span v-if="a.simulated" class="badge badge-info">simulated</span>
          <time class="muted small when" :title="formatDateTime(a.detected_at)">{{ timeAgo(a.detected_at) }}</time>
        </div>
        <p class="output">{{ a.output }}</p>
        <div class="meta">
          <span class="muted small">Container <strong class="ink">{{ a.container_name }}</strong></span>
          <code v-if="a.command">{{ a.command }}</code>
        </div>
        <div class="actions">
          <span v-if="a.acknowledged" class="badge badge-success"><AppIcon name="check" :size="13" />Acknowledged</span>
          <button v-else class="btn btn-outline btn-sm" :disabled="acking.has(a.id)" @click="ack(a)">
            {{ acking.has(a.id) ? 'Marking…' : 'Acknowledge' }}
          </button>
        </div>
      </article>
    </div>
  </div>
</template>

<style scoped>
.small { font-size: 0.82rem; }
.ink { color: var(--ink); }
.live {
  display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.55rem 0.9rem; cursor: pointer;
  background: var(--surface); border: 1px solid var(--border-strong); border-radius: 8px;
  font-size: 0.88rem; font-weight: 600; color: var(--muted);
}
.live input { position: absolute; opacity: 0; pointer-events: none; }
.live .dot { width: 8px; height: 8px; border-radius: 999px; background: var(--border-strong); }
.live.on { color: var(--low); border-color: #BFE0C2; background: var(--low-bg); }
.live.on .dot { background: var(--low); animation: pulse 1.6s ease-in-out infinite; }
.live:has(input:focus-visible) { outline: 2px solid var(--secondary); outline-offset: 2px; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }

.summary { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.1rem; }
.stat { padding: 1rem 1.25rem; display: flex; flex-direction: column; gap: 0.2rem; }
.stat-label { font-size: 0.82rem; font-weight: 600; color: var(--muted); }
.stat-value { font-size: 1.9rem; font-weight: 700; color: var(--primary); line-height: 1.15; }
.stat-value.crit { color: var(--crit); }

.toolbar { display: flex; justify-content: space-between; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
.seg-group { display: flex; gap: 0.4rem; }
.sev-select { width: auto; min-width: 11rem; }

.list { display: flex; flex-direction: column; gap: 0.9rem; }
.alert { padding: 1.1rem 1.25rem; }
.alert.done { opacity: 0.65; }
.alert-top { display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap; margin-bottom: 0.5rem; }
.rule { color: var(--ink); }
.when { margin-left: auto; }
.output { font-size: 0.92rem; margin-bottom: 0.7rem; }
.meta { display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; margin-bottom: 0.85rem; }
.actions { display: flex; justify-content: flex-end; }

@media (max-width: 640px) { .summary { grid-template-columns: 1fr; } }
</style>