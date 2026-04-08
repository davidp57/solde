export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface UserRead {
  id: number
  username: string
  email: string
  role: 'READONLY' | 'SECRETAIRE' | 'TRESORIER' | 'ADMIN'
  is_active: boolean
  created_at: string
}
