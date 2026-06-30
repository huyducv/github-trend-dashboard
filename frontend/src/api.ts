import type { DashboardPayload, RepoDetail, Sector, TopicPayload } from "./types";

const jsonHeaders = { "Content-Type": "application/json" };

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options);
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function fetchDashboard(sector?: string): Promise<DashboardPayload> {
  const params = sector ? `?sector=${encodeURIComponent(sector)}` : "";
  return request<DashboardPayload>(`/api/dashboard${params}`);
}

export function fetchTopics(): Promise<TopicPayload> {
  return request<TopicPayload>("/api/topics");
}

export function fetchSectors(): Promise<{ sectors: Sector[] }> {
  return request<{ sectors: Sector[] }>("/api/config/sectors");
}

export function syncNow(): Promise<{ snapshot_at: string; repositories_seen: number; repositories_saved: number; skipped: number }> {
  return request("/api/sync", { method: "POST", headers: jsonHeaders });
}

export function fetchRepo(owner: string, name: string): Promise<RepoDetail> {
  return request<RepoDetail>(`/api/repos/${encodeURIComponent(owner)}/${encodeURIComponent(name)}`);
}
