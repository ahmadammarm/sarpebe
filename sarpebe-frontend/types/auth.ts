export interface AuthUser {
  id: string;
  email: string | null;
  full_name: string;
  role: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  /** Access token lifetime in seconds. */
  expires_in: number;
  user: AuthUser;
}

export interface MessageResponse {
  message: string;
}
