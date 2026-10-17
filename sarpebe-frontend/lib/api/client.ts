import axios from "axios";
import { getSession } from "next-auth/react";
import { API_BASE_URL } from "./config";

export { API_BASE_URL };

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

export async function getAuthToken(): Promise<string | undefined> {
  const session = await getSession();
  return session?.accessToken;
}

apiClient.interceptors.request.use(async (config) => {
  const token = await getAuthToken();

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});
