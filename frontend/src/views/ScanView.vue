<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { scanImage, listScans, getScanVulnerabilities } from '../services/scanService'
import { formatDateTime, riskBadgeClass } from '../utils/format'
import PageHeader from '../components/PageHeader.vue'
import AppIcon from '../components/AppIcon.vue'
import SeverityBadge from '../components/SeverityBadge.vue'

const router = useRouter()
const examples = ['nginx:latest', 'ubuntu:20.04', 'python:3.9', 'node:16', 'alpine:3.18']
const severityKeys = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']

/* ---- scan form + history ---- */
const imageInput = ref('')
const scanning = ref(false)
const scanError = ref('')
const scans = ref([])
const loadingScans = ref(false)

async function loadScans() {
  loadingScans.value = true
  try {
    scans.value = await listScans()
  } catch {
    scans.value = []
  } finally {
    loadingScans.value = false
  }
}

async function runScan() {
  const image = imageInput.value.trim()
  if (!image) return
  scanning.value = true
  scanError.value = ''
  try {
    await scanImage(image)
    imageInput.value = ''
    await loadScans()
  } catch (e) {
    scanError.value = e.response?.data?.detail || "Couldn't reach the scanner. Check that the backend is running."
  } finally {
    scanning.value = false
  }
}

/* ---- CVE detail modal ---- */
const detail = ref(null)
const detailLoading = ref(false)
const detailError = ref('')
const sevFilter = ref('ALL')
const query = ref('')

async function openDetail(scan) {
  detail.value = { id: scan.id, image: scan.image, scanned_at: scan.scanned_at, vulnerabilities: [] }
  detailLoading.value = true
  detailError.value = ''
  sevFilter.value = 'ALL'
  query.value = ''
  try {
    detail.value = await getScanVulnerabilities(scan.id)
  } catch {
    detailError.value = "Couldn't load the vulnerability list for this scan."
  } finally {
    detailLoading.value = false
  }
}
function closeDetail() { detail.value = null }

const detailCounts = computed(() => {
  const c = { ALL: 0, CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 }
  for (const v of detail.value?.vulnerabilities || []) {
    c.ALL++
    if (c[v.Severity] !== undefined) c[v.Severity]++
  }
  return c
})
const filteredVulns = computed(() => {
  const q = query.value.trim().toLowerCase()
  return (detail.value?.vulnerabilities || []).filter((v) =>
    (sevFilter.value === 'ALL' || v.Severity === sevFilter.value) &&
    (!q || `${v.VulnerabilityID} ${v.PkgName}`.toLowerCase().includes(q)))
})

/** Jump to the AI page with this CVE pre-filled. */
function explain(v) {
  router.push({
    name: 'ai',
    query: { cve: v.VulnerabilityID, pkg: v.PkgName, sev: v.Severity, desc: (v.Title || v.Description || '').slice(0, 300) },
  })
}

function onKey(e) { if (e.key === 'Escape') closeDetail() }
onMounted(() => { loadScans(); window.addEventListener('keydown', onKey) })
onUnmounted(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <div class="page">
    <PageHeader title="Image scans" crumb="Image scans"
                subtitle="Scan a Docker image with Trivy and review every known CVE by severity." />

    <section class="card">
      <div class="card-body">
        <form class="scan-form" @submit.prevent="runScan">
          <div class="field grow">
            <label for="image">Docker image</label>
            <input id="image" v-model="imageInput" class="input" placeholder="e.g. nginx:latest"
                   :disabled="scanning" autocomplete="off" />
          </div>
          <button class="btn btn-brand" :disabled="scanning || !imageInput.trim()">
            <AppIcon name="scan" :size="16" />{{ scanning ? 'Scanning…' : 'Scan image' }}
          </button>
        </form>
        <div class="examples">
          <span class="muted small">Try:</span>
          <button v-for="e in examples" :key="e" type="button" class="chip" :disabled="scanning" @click="imageInput = e">{{ e }}</button>
        </div>
        <p v-if="scanError" class="banner-error" role="alert">{{ scanError }}</p>
        <p v-if="scanning" class="muted hint">Scanning… the first scan downloads Trivy's vulnerability database and can take a minute or two.</p>
      </div>
    </section>

    <section class="card">
      <header class="card-head">
        <h2>Scan history</h2>
        <button class="btn btn-outline btn-sm" :disabled="loadingScans" @click="loadScans">
          <AppIcon name="refresh" :size="14" />Refresh
        </button>
      </header>
      <div v-if="loadingScans && !scans.length" class="empty">Loading…</div>
      <div v-else-if="!scans.length" class="empty"><strong>No scans yet</strong>Run your first scan above.</div>
      <div v-else class="table-wrap">
        <table class="table">
          <thead>
            <tr><th>Image</th><th>Scanned</th><th>By</th><th>Critical · High · Medium · Low</th><th>Total</th><th>Risk</th><th></th></tr>
          </thead>
          <tbody>
            <tr v-for="s in scans" :key="s.id">
              <td class="strong">{{ s.image }}</td>
              <td class="muted">{{ formatDateTime(s.scanned_at) }}</td>
              <td class="muted">{{ s.scanned_by }}</td>
              <td>
                <div class="mini">
                  <span v-for="k in severityKeys" :key="k" class="mini-pill" :class="[k.toLowerCase(), { zero: !s.severity_counts[k] }]" :title="k">
                    {{ s.severity_counts[k] || 0 }}
                  </span>
                </div>
              </td>
              <td>{{ s.total }}</td>
              <td><span class="badge" :class="riskBadgeClass(s.risk_score)">{{ s.risk_score }}</span></td>
              <td><button class="btn btn-outline btn-sm" @click="openDetail(s)">View CVEs</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <div v-if="detail" class="overlay" @click.self="closeDetail">
      <div class="modal card" role="dialog" aria-modal="true" :aria-label="`Vulnerabilities for ${detail.image}`">
        <header class="card-head">
          <div>
            <h2>{{ detail.image }}</h2>
            <span class="muted small">Scanned {{ formatDateTime(detail.scanned_at) }}</span>
          </div>
          <button class="btn-quiet" @click="closeDetail">Close</button>
        </header>

        <div class="modal-tools">
          <div class="filters">
            <button v-for="k in ['ALL', ...severityKeys]" :key="k" class="chip" :class="{ active: sevFilter === k }" @click="sevFilter = k">
              {{ k === 'ALL' ? 'All' : k.charAt(0) + k.slice(1).toLowerCase() }} ({{ detailCounts[k] }})
            </button>
          </div>
          <input v-model="query" class="input search" placeholder="Search CVE ID or package" />
        </div>

        <div class="modal-body">
          <p v-if="detailLoading" class="muted">Loading vulnerabilities…</p>
          <p v-else-if="detailError" class="banner-error">{{ detailError }}</p>
          <div v-else-if="!detail.vulnerabilities.length" class="empty"><strong>No vulnerabilities found</strong>This image came back clean.</div>
          <div v-else-if="!filteredVulns.length" class="empty"><strong>No matches</strong>Try a different filter.</div>
          <ul v-else class="cve-list">
            <li v-for="(v, i) in filteredVulns" :key="i">
              <div class="cve-top">
                <SeverityBadge :level="v.Severity" />
                <strong>{{ v.VulnerabilityID }}</strong>
                <span class="muted small">{{ v.PkgName }} · {{ v.InstalledVersion }}</span>
                <button class="btn btn-outline btn-sm explain" @click="explain(v)"><AppIcon name="spark" :size="14" />Explain with AI</button>
              </div>
              <p class="cve-title">{{ v.Title || 'No description available.' }}</p>
              <p v-if="v.FixedVersion" class="fix">Fixed in <code>{{ v.FixedVersion }}</code></p>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.small { font-size: 0.82rem; }
.strong { font-weight: 600; color: var(--ink); }
.scan-form { display: flex; gap: 0.75rem; align-items: flex-end; }
.examples { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.9rem; }
.hint { margin-top: 0.75rem; font-size: 0.85rem; }
.banner-error { margin-top: 0.9rem; }

.mini { display: flex; gap: 0.3rem; }
.mini-pill { min-width: 2rem; text-align: center; font-size: 0.78rem; font-weight: 700; padding: 0.12rem 0.4rem; border-radius: 6px; }
.mini-pill.critical { color: var(--crit); background: var(--crit-bg); }
.mini-pill.high { color: var(--high); background: var(--high-bg); }
.mini-pill.medium { color: #9A6700; background: var(--med-bg); }
.mini-pill.low { color: var(--low); background: var(--low-bg); }
.mini-pill.zero { color: var(--muted); background: var(--surface-2); font-weight: 600; }

.overlay {
  position: fixed; inset: 0; background: rgba(11, 34, 64, 0.5); z-index: 200;
  display: flex; align-items: center; justify-content: center; padding: 1.5rem;
}
.modal { width: 100%; max-width: 46rem; max-height: 86vh; display: flex; flex-direction: column; box-shadow: var(--shadow-md); }
.modal-tools { display: flex; gap: 0.75rem; align-items: center; justify-content: space-between; flex-wrap: wrap; padding: 0.9rem 1.25rem; border-bottom: 1px solid var(--border); }
.filters { display: flex; gap: 0.4rem; flex-wrap: wrap; }
.search { max-width: 14rem; padding: 0.4rem 0.7rem; font-size: 0.85rem; }
.modal-body { padding: 0.5rem 1.25rem 1.25rem; overflow-y: auto; }
.cve-list { list-style: none; margin: 0; padding: 0; }
.cve-list li { padding: 0.95rem 0; border-bottom: 1px solid var(--border); }
.cve-list li:last-child { border-bottom: 0; }
.cve-top { display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap; margin-bottom: 0.35rem; }
.explain { margin-left: auto; }
.cve-title { font-size: 0.9rem; }
.fix { font-size: 0.82rem; color: var(--muted); margin-top: 0.3rem; }

@media (max-width: 640px) { .scan-form { flex-direction: column; align-items: stretch; } }
</style>