import apiClient from './client'
import type { UserRead, UserRole } from './types'

export interface UserCreatePayload {
  username: string
  email: string
  password: string
  role: UserRole
}

export interface UserAdminUpdatePayload {
  role?: UserRole
  is_active?: boolean
}

export async function listUsersApi(): Promise<UserRead[]> {
  const response = await apiClient.get<UserRead[]>('/api/auth/users')
  return response.data
}

export async function createUserApi(payload: UserCreatePayload): Promise<UserRead> {
  const response = await apiClient.post<UserRead>('/api/auth/users', payload)
  return response.data
}

export async function updateUserApi(
  userId: number,
  payload: UserAdminUpdatePayload,
): Promise<UserRead> {
  const response = await apiClient.patch<UserRead>(`/api/auth/users/${userId}`, payload)
  return response.data
}