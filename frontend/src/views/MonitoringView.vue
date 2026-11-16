<script setup>
import { computed, onMounted, ref } from 'vue'
import { getHealth } from '../services/systemService'
import { getAiStatus } from '../services/aiService'
import PageHeader from '../components/PageHeader.vue'
import AppIcon from '../components/AppIcon.vue'

/**
 * Metrics & service health page.
 *
 * Probes the backend, database and AI engine, shows their status, and embeds the
 * Grafana dashboard that is fed by Prometheus.
 */
// Where the Grafana dashboard is reachable from the browser (host ports from docker-compose.yml).
const GRAFANA_URL = 'http://localhost:3000'
const DASHBOARD_PATH = '/d/aegiscloud-overview'

const loading = ref(true)
const health = ref(null) // { status, database, latency, trivy } or null when unreachable
const ai = ref(null)     // { provider, model, configured } or null
const checkedAt = ref(null)

/** Probe the backend, database and AI engine. Each probe is independent, so one failure never hides the others. */
async function check() {
  loading.value = true
  const [h, a] = await Promise.allSettled([getHealth(), getAiStatus()])
  health.value = h.status === 'fulfilled' ? h.value : null
  ai.value = a.status === 'fulfilled' ? a.value : null
  checkedAt.value = new Date()
  loading.value = false
}
onMounted(check)

/** Visual style for each status key used in the table. */
const STATE = {
  up: { label: 'Operational', cls: 'badge-success' },
  down: { label: 'Unreachable', cls: 'badge-danger' },
  unknown: { label: 'Unknown', cls: 'badge-neutral' },
  config: { label: 'Not configured', cls: 'badge-warn' },
  demo: { label: 'Simulated', cls: 'badge-info' },
}

/** Rows shown in the service status table. */
const services = computed(() => [
  {
    name: 'Backend API', detail: 'FastAPI',
    state: health.value ? 'up' : 'down',
    note: health.value ? `${health.value.latency} ms response` : 'No response from /health',
  },
  {
    name: 'Database', detail: 'MongoDB',
    state: !health.value ? 'unknown' : health.value.database === 'up' ? 'up' : 'down',
    note: !health.value
      ? 'Backend unreachable'
      : health.value.database === 'up' ? 'Connection healthy' : 'Backend cannot reach MongoDB',
  },
  {
    name: 'AI engine', detail: 'Google Gemini (Google Cloud)',
    state: !ai.value ? 'unknown' : ai.value.configured ? 'up' : 'config',
    note: !ai.value
      ? 'Backend unreachable'
      : ai.value.configured ? `Model ${ai.value.model}` : 'Add GEMINI_API_KEY to backend/.env',
  },
  {
    name: 'Runtime detection', detail: 'Falco',
    state: 'demo',
    note: 'Demo mode: alerts come from scripts/simulate_falco_attack.py',
  },
  {
    name: 'Metrics collection', detail: 'Prometheus',
    state: health.value ? 'up' : 'unknown',
    note: 'Scraping the backend every 15 seconds (Docker)',
  },
  {
    name: 'Dashboards', detail: 'Grafana',
    state: health.value ? 'up' : 'unknown',
    note: 'Dashboard provisioned from monitoring/grafana (Docker)',
  },
])

/** True when the two core services (backend and database) are both healthy. */
const coreUp = computed(() => services.value.slice(0, 2).every((s) => s.state === 'up'))
</script>

<template>
  <div class="page">
    <PageHeader title="Metrics &amp; service health" crumb="Metrics"
                subtitle="Live status of the services AegisCloud depends on.">
      <button class="btn btn-outline" :disabled="loading" @click="check">
        <AppIcon name="refresh" :size="16" />{{ loading ? 'Checking…' : 'Recheck' }}
      </button>
    </PageHeader>

    <div class="overall" :class="coreUp ? 'ok' : 'bad'" role="status">
      <AppIcon :name="coreUp ? 'shield' : 'bell'" :size="20" />
      <div>
        <strong>{{ loading ? 'Checking services…' : coreUp ? 'All core services are operational' : 'Some core services need attention' }}</strong>
        <span v-if="checkedAt" class="when">Last checked {{ checkedAt.toLocaleTimeString() }}</span>
      </div>
    </div>

    <section class="card">
      <header class="card-head"><h2>Service status</h2></header>
      <div class="table-wrap">
        <table class="table">
          <thead><tr><th>Service</th><th>Technology</th><th>Status</th><th>Details</th></tr></thead>
          <tbody>
            <tr v-for="s in services" :key="s.name">
              <td class="strong">{{ s.name }}</td>
              <td class="muted">{{ s.detail }}</td>
              <td><span class="badge" :class="STATE[s.state].cls">{{ STATE[s.state].label }}</span></td>
              <td class="muted">{{ s.note }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="card">
      <header class="card-head">
        <h2>Live dashboard</h2>
        <a class="btn btn-outline btn-sm" :href="GRAFANA_URL + DASHBOARD_PATH" target="_blank" rel="noopener">
          Open in Grafana
        </a>
      </header>
      <div class="card-body embed">
        <iframe
          :src="GRAFANA_URL + DASHBOARD_PATH + '?orgId=1&kiosk&theme=light&refresh=10s'"
          title="AegisCloud Grafana dashboard"
          loading="lazy"
        ></iframe>
      </div>
    </section>
  </div>
</template>

<style scoped>
.strong { font-weight: 600; color: var(--ink); }
.overall {
  display: flex; align-items: center; gap: 0.85rem; padding: 0.95rem 1.25rem;
  border-radius: var(--radius); border: 1px solid; font-size: 0.95rem;
}
.overall.ok { background: var(--low-bg); border-color: #BFE0C2; color: #1E5B22; }
.overall.bad { background: var(--crit-bg); border-color: #F3C4C4; color: #8E1B1B; }
.overall div { display: flex; flex-direction: column; }
.when { font-size: 0.8rem; opacity: 0.8; }
.embed { padding: 0; }
.embed iframe {
  width: 100%; height: 620px; border: 0; display: block;
  border-radius: 0 0 var(--radius) var(--radius);
}
</style>