/// <reference types="vite/client" />

declare const __APP_VERSION__: string

interface ImportMetaEnv {
	readonly VITE_DEV_AUTO_LOGIN?: string
	readonly VITE_DEV_AUTO_LOGIN_USERNAME?: string
	readonly VITE_DEV_AUTO_LOGIN_PASSWORD?: string
}

interface ImportMeta {
	readonly env: ImportMetaEnv
}

import 'vue-router'
declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    requiresAccounting?: boolean
    requiresManagement?: boolean
    requiresAdmin?: boolean
    /** i18n key for this page's breadcrumb label */
    label?: string
    /** Parent route for nested breadcrumbs (e.g. contact-history under contacts) */
    breadcrumbParent?: { labelKey: string; to: string }
  }
}
