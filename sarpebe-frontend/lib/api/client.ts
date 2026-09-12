import axios from "axios";
import { getSession } from "next-auth/react";

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

apiClient.interceptors.request.use(async (config) => {
  // Try to get session from NextAuth
  const session = await getSession();
  
  // Cast session to access our custom token property
  const token = (session as any)?.supabaseAccessToken;
  
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  
  return config;
});
