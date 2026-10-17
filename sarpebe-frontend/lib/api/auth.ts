import axios from "axios";
import { API_BASE_URL } from "./config";
import type { MessageResponse, TokenResponse } from "@/types/auth";
import type { ForgotPasswordInput, RegisterInput, ResetPasswordInput } from "@/lib/utils/validators";

// Deliberately separate from `apiClient`: these endpoints are unauthenticated, and NextAuth
// calls login/refresh/logout on the server where there is no browser session to read.
const authClient = axios.create({
  baseURL: `${API_BASE_URL}/api/auth`,
  headers: { "Content-Type": "application/json" },
});

export async function loginRequest(email: string, password: string): Promise<TokenResponse> {
  const res = await authClient.post<TokenResponse>("/login", { email, password });
  return res.data;
}

export async function refreshRequest(refreshToken: string): Promise<TokenResponse> {
  const res = await authClient.post<TokenResponse>("/refresh", { refresh_token: refreshToken });
  return res.data;
}

export async function logoutRequest(refreshToken: string): Promise<void> {
  await authClient.post("/logout", { refresh_token: refreshToken });
}

export async function registerAccount(input: RegisterInput): Promise<MessageResponse> {
  const res = await authClient.post<MessageResponse>("/register", {
    email: input.email,
    password: input.password,
    full_name: input.fullName,
  });
  return res.data;
}

export async function verifyEmail(token: string): Promise<MessageResponse> {
  const res = await authClient.post<MessageResponse>("/verify-email", { token });
  return res.data;
}

export async function resendVerification(email: string): Promise<MessageResponse> {
  const res = await authClient.post<MessageResponse>("/resend-verification", { email });
  return res.data;
}

export async function forgotPassword(input: ForgotPasswordInput): Promise<MessageResponse> {
  const res = await authClient.post<MessageResponse>("/forgot-password", { email: input.email });
  return res.data;
}

export async function resetPassword(token: string, input: ResetPasswordInput): Promise<MessageResponse> {
  const res = await authClient.post<MessageResponse>("/reset-password", {
    token,
    password: input.password,
  });
  return res.data;
}
