/**
 * Date and risk helpers shared by every view.
 *
 * MongoDB returns datetimes as UTC but the API serialises them without a "Z",
 * so `new Date(value)` would read them as *local* time and show the wrong hour.
 * parseDate() fixes that by treating zone-less timestamps as UTC.
 */

/** Parse an API timestamp into a Date (zone-less strings are treated as UTC). */
export function parseDate(value) {
  if (!value) return null
  const s = String(value)
  const hasZone = /([zZ]|[+-]\d{2}:?\d{2})$/.test(s)
  return new Date(hasZone ? s : s + 'Z')
}

/** "29 Sept 2026, 10:40 am" in the viewer's local time. */
export function formatDateTime(value) {
  const d = parseDate(value)
  return d ? d.toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) : '-'
}

/** "just now", "5 min ago", "3 h ago", "2 d ago". */
export function timeAgo(value) {
  const d = parseDate(value)
  if (!d) return '-'
  const seconds = Math.max(0, (Date.now() - d.getTime()) / 1000)
  if (seconds < 60) return 'just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)} min ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} h ago`
  return `${Math.floor(seconds / 86400)} d ago`
}

/** Human label for a 0-100 risk score. */
export function riskLabelFor(score) {
  if (score < 20) return 'Low'
  if (score < 50) return 'Moderate'
  if (score < 80) return 'High'
  return 'Critical'
}

/** Badge class (see main.css) matching a 0-100 risk score. */
export function riskBadgeClass(score) {
  if (score < 20) return 'badge-success'
  if (score < 50) return 'badge-warn'
  if (score < 80) return 'badge-high'
  return 'badge-danger'
}