/**
 * English translations skeleton for Solde ⚖️
 *
 * Status: partial — only app / auth / common are translated.
 * All other sections are absent; missing keys fall back to French via fallbackLocale: 'fr'.
 *
 * CHR-078 — progressively add and translate the remaining sections.
 */
export default {
  app: {
    name: 'Solde ⚖️',
    active_fiscal_year: 'Active fiscal year',
    all_fiscal_years: 'All fiscal years',
  },
  auth: {
    login: {
      title: 'Sign in',
      subtitle: 'Non-profit accounting',
      username: 'Username',
      password: 'Password',
      submit: 'Sign in',
      reset_hint:
        'Forgot your password? Ask an administrator to temporarily reset your access.',
      error: {
        invalid: 'Invalid username or password.',
        network: 'Unable to reach the server. Please try again.',
        unknown: 'An unexpected error occurred.',
      },
    },
    logout: 'Sign out',
    dark_mode: 'Dark mode',
    light_mode: 'Light mode',
    me: 'My account',
  },
  common: {
    loading: 'Loading…',
    save: 'Save',
    search: 'Search',
    cancel: 'Cancel',
    discard: 'Discard changes',
    unsaved_changes: 'Unsaved changes',
    unsaved_changes_confirm: 'Unsaved changes will be lost. Continue anyway?',
    delete: 'Delete',
    yes: 'Yes',
    no: 'No',
    date_filter_placeholder: 'DD/MM/YYYY',
    confirm: 'Confirm',
    all: 'All',
    actions: 'Actions',
    filter_placeholder: 'Search…',
    refresh: 'Refresh',
    reset_filters: 'Reset filters',
    previous: 'Previous',
    next: 'Next',
    empty: 'No data.',
    active: 'Active',
    inactive: 'Inactive',
    list: {
      count_total: '{count} item(s)',
      count_filtered: '{shown} of {total}',
      search_chip: 'Search: {query}',
      filter_chip: 'Filter: {label}',
      column_filters_chip: '{count} column filter(s)',
      status: {
        loading: 'Updating list.',
        empty: 'No items to display.',
        filtered_empty: 'No results match the active filters.',
        filtered_scope: 'View restricted by active filters and search.',
        full_scope: 'Showing all items in the current scope.',
      },
    },
    error: {
      unknown: 'An error occurred.',
      forbidden: 'Access denied.',
      notFound: 'Resource not found.',
    },
    api_limit_warning:
      'Display limit reached (1,000 items). Results may be incomplete — refine the filters to reduce the loaded volume.',
  },
}
