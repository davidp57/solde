/**
 * User role constants — single source of truth for role strings.
 * Use these instead of raw string literals throughout the frontend.
 */
export const USER_ROLES = {
  ADMIN: 'admin',
  TRESORIER: 'tresorier',
  SECRETAIRE: 'secretaire',
  READONLY: 'readonly',
} as const

export type UserRoleKey = keyof typeof USER_ROLES
