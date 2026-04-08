import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import LoginView from '../views/LoginView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { requiresAuth: false },
    },
    {
      path: '/',
      redirect: '/dashboard',
    },
    {
      path: '/',
      component: () => import('../layouts/AppLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: 'dashboard',
          name: 'dashboard',
          component: () => import('../views/DashboardView.vue'),
        },
        {
          path: 'contacts',
          name: 'contacts',
          component: () => import('../views/ContactsView.vue'),
        },
        {
          path: 'accounting/accounts',
          name: 'accounting-accounts',
          component: () => import('../views/AccountingAccountsView.vue'),
        },
        {
          path: 'invoices/client',
          name: 'invoices-client',
          component: () => import('../views/ClientInvoicesView.vue'),
        },
        {
          path: 'invoices/supplier',
          name: 'invoices-supplier',
          component: () => import('../views/SupplierInvoicesView.vue'),
        },
        {
          path: 'settings',
          name: 'settings',
          component: () => import('../views/SettingsView.vue'),
          meta: { requiresAdmin: true },
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/dashboard',
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  // Restore tokens from localStorage on first navigation
  if (auth.accessToken === null) {
    auth.initFromStorage()
    if (auth.accessToken && !auth.user) {
      await auth.fetchMe()
    }
  }

  if (to.meta.requiresAuth === false) {
    // Public route — redirect authenticated users away from login
    if (auth.isAuthenticated && to.name === 'login') {
      return { name: 'dashboard' }
    }
    return true
  }

  if (!auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return { name: 'dashboard' }
  }

  return true
})

export default router
