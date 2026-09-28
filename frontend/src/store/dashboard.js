import { defineStore } from 'pinia'
import api from '../services/api'

export const useDashboardStore = defineStore('dashboard', {
  state: () => ({
    summary: null,
    loading: false,
    error: '',
  }),
  actions: {
    async load() {
      this.loading = true
      this.error = ''
      try {
        this.summary = (await api.get('/dashboard/summary')).data
      } catch {
        this.error = "Couldn't load the dashboard. Check that the API is running."
      } finally {
        this.loading = false
      }
    },
  },
})