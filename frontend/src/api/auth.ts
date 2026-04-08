import axios from 'axios'
import type { LoginRequest, TokenResponse, UserRead } from './types'

export async function loginApi(request: LoginRequest): Promise<TokenResponse> {
  // FastAPI OAuth2PasswordRequestForm expects form data
  const form = new URLSearchParams()
  form.append('username', request.username)
  form.append('password', request.password)

  const response = await axios.post<TokenResponse>('/api/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return response.data
}

export async function refreshApi(refreshToken: string): Promise<TokenResponse> {
  const response = await axios.post<TokenResponse>('/api/auth/refresh', {
    refresh_token: refreshToken,
  })
  return response.data
}

export async function getMeApi(accessToken: string): Promise<UserRead> {
  const response = await axios.get<UserRead>('/api/auth/me', {
    headers: { Authorization: `Bearer ${accessToken}` },
  })
  return response.data
}
