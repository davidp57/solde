import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import LoginView from '../views/LoginView.vue'
import NotFoundView from '../views/NotFoundView.vue'

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
          meta: { label: 'nav.dashboard' },
        },
        {
          path: 'profile',
          name: 'profile',
          component: () => import('../views/ProfileView.vue'),
          meta: { label: 'nav.profile' },
        },
        {
          path: 'contacts',
          name: 'contacts',
          component: () => import('../views/ContactsView.vue'),
          meta: { requiresManagement: true, label: 'nav.contacts' },
        },
        {
          path: 'contacts/:id/history',
          name: 'contact-history',
          component: () => import('../views/ContactDetailView.vue'),
          meta: { requiresManagement: true, label: 'contact_history.title' },
        },
        {
          path: 'accounting/accounts',
          name: 'accounting-accounts',
          component: () => import('../views/AccountingAccountsView.vue'),
          meta: { requiresAccounting: true, label: 'nav.accounting_accounts' },
        },
        {
          path: 'invoices/client',
          name: 'invoices-client',
          component: () => import('../views/ClientInvoicesView.vue'),
          meta: { requiresManagement: true, label: 'nav.invoices_client' },
        },
        {
          path: 'invoices/supplier',
          name: 'invoices-supplier',
          component: () => import('../views/SupplierInvoicesView.vue'),
          meta: { requiresManagement: true, label: 'nav.invoices_supplier' },
        },
        {
          path: 'payments',
          name: 'payments',
          component: () => import('../views/PaymentsView.vue'),
          meta: { requiresManagement: true, label: 'nav.payments' },
        },
        {
          path: 'cash',
          name: 'cash',
          component: () => import('../views/CashView.vue'),
          meta: { requiresManagement: true, label: 'nav.cash' },
        },
        {
          path: 'bank',
          name: 'bank',
          component: () => import('../views/BankView.vue'),
          meta: { requiresManagement: true, label: 'nav.bank' },
        },
        {
          path: 'accounting/journal',
          name: 'accounting-journal',
          component: () => import('../views/AccountingJournalView.vue'),
          meta: { requiresAccounting: true, label: 'nav.accounting_journal' },
        },
        {
          path: 'accounting/balance',
          name: 'accounting-balance',
          component: () => import('../views/AccountingBalanceView.vue'),
          meta: { requiresAccounting: true, label: 'nav.accounting_balance' },
        },
        {
          path: 'accounting/ledger',
          name: 'accounting-ledger',
          component: () => import('../views/AccountingLedgerView.vue'),
          meta: { requiresAccounting: true, label: 'nav.accounting_ledger' },
        },
        {
          path: 'accounting/resultat',
          name: 'accounting-resultat',
          component: () => import('../views/AccountingResultatView.vue'),
          meta: { requiresAccounting: true, label: 'nav.accounting_resultat' },
        },
        {
          path: 'accounting/bilan',
          name: 'accounting-bilan',
          component: () => import('../views/AccountingBilanView.vue'),
          meta: { requiresAccounting: true, label: 'nav.accounting_bilan' },
        },
        {
          path: 'accounting/rules',
          name: 'accounting-rules',
          component: () => import('../views/AccountingRulesView.vue'),
          meta: { requiresAccounting: true, label: 'nav.accounting_rules' },
        },
        {
          path: 'accounting/fiscal-years',
          name: 'accounting-fiscal-years',
          component: () => import('../views/FiscalYearView.vue'),
          meta: { requiresAccounting: true, label: 'nav.accounting_fiscal_years' },
        },
        {
          path: 'salaries',
          name: 'salaries',
          component: () => import('../views/SalaryView.vue'),
          meta: { requiresManagement: true, label: 'nav.salaries' },
        },
        {
          path: 'employees',
          name: 'employees',
          component: () => import('../views/EmployeesView.vue'),
          meta: { requiresManagement: true, label: 'nav.employees' },
        },
        {
          path: 'import/excel',
          name: 'import-excel',
          component: () => import('../views/ImportExcelView.vue'),
          meta: { requiresAdmin: true, label: 'nav.import_excel' },
        },
        {
          path: 'import/history',
          name: 'import-history',
          component: () => import('../views/ImportHistoryView.vue'),
          meta: { requiresAdmin: true, label: 'nav.import_history' },
        },
        {
          path: 'settings',
          name: 'settings',
          component: () => import('../views/SettingsView.vue'),
          meta: { requiresAdmin: true, label: 'nav.settings' },
        },
        {
          path: 'users',
          name: 'users',
          component: () => import('../views/UsersView.vue'),
          meta: { requiresAdmin: true, label: 'nav.users' },
        },
        {
          path: 'system',
          name: 'system',
          component: () => import('../views/SystemView.vue'),
          meta: { requiresAdmin: true, label: 'nav.system' },
        },
        {
          path: 'aide',
          name: 'aide',
          component: () => import('../views/HelpView.vue'),
          meta: { label: 'nav.help' },
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: NotFoundView,
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
    if (!auth.accessToken) {
      await auth.maybeAutoLoginForDev()
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

  // Force password change: only allow access to the profile page
  if (auth.mustChangePassword && to.name !== 'profile') {
    return { name: 'profile' }
  }

  if (to.meta.requiresAccounting && !auth.canAccessAccounting) {
    return { name: 'dashboard' }
  }

  if (to.meta.requiresManagement && !auth.canAccessManagement) {
    return { name: 'dashboard' }
  }

  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return { name: 'dashboard' }
  }

  return true
})

export default router
