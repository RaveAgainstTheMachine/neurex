import { API_BASE } from "./config";
import { useStore } from "./store";
import toast from "react-hot-toast";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const state = useStore.getState();
  const token = state.token;

  const headers = new Headers(options.headers || {});
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    if (token) {
      state.logout();
      throw new Error("Session expired");
    }
    throw new Error("Unauthorized access");
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || response.statusText);
  }

  if (response.status === 204) return {} as T;
  const text = await response.text();
  try {
    return text ? JSON.parse(text) : {} as T;
  } catch (err) {
    return {} as T;
  }
}

export const api = {
  get: <T>(path: string, options?: RequestInit) => request<T>(path, { ...options, method: "GET" }),
  post: <T>(path: string, body?: any, options?: RequestInit) => 
    request<T>(path, { 
      ...options, 
      method: "POST", 
      headers: { "Content-Type": "application/json", ...options?.headers },
      body: body ? JSON.stringify(body) : undefined 
    }),
  put: <T>(path: string, body?: any, options?: RequestInit) => 
    request<T>(path, { 
      ...options, 
      method: "PUT", 
      headers: { "Content-Type": "application/json", ...options?.headers },
      body: body ? JSON.stringify(body) : undefined 
    }),
  delete: <T>(path: string, options?: RequestInit) => request<T>(path, { ...options, method: "DELETE" }),
};
