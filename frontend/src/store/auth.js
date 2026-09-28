import { defineStore } from 'pinia'
import * as authService from '../services/authService'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('aegis_token'),
    user: null,
  }),
  getters: {
    isAuthenticated: (s) => !!s.token,
  },
  actions: {
    _set({ access_token, user }) {
      this.token = access_token
      this.user = user
      localStorage.setItem('aegis_token', access_token)
    },
    async login(email, password) {
      this._set(await authService.login(email, password))
    },
    async register(name, email, password) {
      this._set(await authService.register(name, email, password))
    },
    async restore() {
      if (!this.token || this.user) return
      try {
        this.user = await authService.fetchMe()
      } catch {
        this.logout()
      }
    },
    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('aegis_token')
    },
  },
})